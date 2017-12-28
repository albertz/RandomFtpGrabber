
import sys
from queue import Queue
from threading import Event, Thread
import better_exchook
import Persistence
import Logging


kNumWorkers = 5
kMinQueuedActions = kNumWorkers  # fill workerQueue always up to N elements, via the watcher thread
kSuggestedMaxQueuedActions = kNumWorkers * 2


# Reloads should work.
if "mainLoopQueue" not in vars():
    mainLoopQueue = Queue()
if "exitEvent" not in vars():
    exitEvent = Event()
if "workerQueue" not in vars():
    workerQueue = None  # type: Queue
if "currentWork" not in vars():
    currentWork = None  # type: set


def setup():
    import Action
    global workerQueue
    global currentWork
    if workerQueue is None:
        workerQueue = Persistence.load("workerQueue.db", Queue, env=vars(Action))
    if currentWork is None:
        currentWork = Persistence.load("currentWork.db", set, env=vars(Action))

    _init_watcher_thread()
    _init_worker_threads()


def queue_work(func):
    """
    :param Action.BaseAction func:
    """
    if currentWork in currentWork:
        Logging.log("queueWork: already in queue: %r" % func)
        return  # just ignore
    currentWork.add(func)
    # noinspection PyUnresolvedReferences
    currentWork.save()
    workerQueue.put(func)
    # noinspection PyUnresolvedReferences
    workerQueue.save()


def reached_suggested_max_queue():
    return len(currentWork) >= kSuggestedMaxQueuedActions


def main_loop():
    """
    We assume this runs in the main-thread.
    """
    while True:
        func = mainLoopQueue.get()
        func()


def worker_loop():
    better_exchook.install()
    while True:
        func = workerQueue.get()
        Logging.log("Next work item: %s" % func, "remaining: %i" % workerQueue.qsize())
        try:
            func()
        except SystemExit:
            return
        except Exception:
            Logging.log_exception("Worker", *sys.exc_info())
        finally:
            # Note, this is buggy:
            # In case that func() adds itself back to the work-queue,
            # we would remove it here and then sometime later when we
            # execute it again, it's not in the set anymore.
            # Note that some other code also does not expect this.
            # TODO fix this
            if func in currentWork:
                currentWork.remove(func)
                # noinspection PyUnresolvedReferences
                currentWork.save()


def watcher_loop():
    import main
    import Action
    better_exchook.install()

    while not exitEvent.isSet():
        if main.DownloadOnly:
            if len(currentWork) == 0:
                queue_work(Action.CheckDownloadsFinished())
            exitEvent.wait(1)
            continue

        if workerQueue.qsize() >= kMinQueuedActions:
            exitEvent.wait(1)
            continue

        func = Action.get_new_action()
        workerQueue.put(func)


if "workers" not in vars():
    workers = []
if "watcher" not in vars():
    watcher = None


def _init_worker_threads():
    if len(workers) >= kNumWorkers:
        return
    assert not workers  # needs fixing otherwise
    # Build up set of actions in the queue.
    current_work_real = set()
    for func in list(workerQueue.queue):
        current_work_real.add(func)
    # Add all missing actions.
    # Those are actions which have been run when we quit last time.
    missing_work = currentWork - current_work_real
    for func in missing_work:
        workerQueue.put(func)
    # Fixup current work set.
    currentWork.update(current_work_real)
    # Now init the threads.
    for i in range(kNumWorkers - len(workers)):
        thread = Thread(target=worker_loop, name="Worker %i/%i" % (i + 1, kNumWorkers))
        workers.append(thread)
        thread.daemon = True
        thread.start()


def _init_watcher_thread():
    global watcher
    if watcher:
        return
    watcher = Thread(target=watcher_loop, name="Watcher")
    watcher.daemon = True
    watcher.start()



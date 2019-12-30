
import sys
from queue import Queue
from threading import Event, Thread, Lock, RLock
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
    currentWorkSet = None  # type: set
if "workerQueueSet" not in vars():
    workerQueueSet = set()
if "lock" not in vars():
    lock = RLock()


def setup():
    import Action
    global workerQueue
    global currentWorkSet
    if workerQueue is None:
        workerQueue = Persistence.load("workerQueue.db", Queue, env=vars(Action))
    if currentWorkSet is None:
        currentWorkSet = Persistence.load("currentWork.db", set, env=vars(Action))

    _init_watcher_thread()
    _init_worker_threads()


def queue_work(func):
    """
    :param Action.BaseAction func:
    """
    with lock:
        if func in workerQueueSet:
            Logging.log("queueWork: already in queue: %r" % func)
            return  # ignore
        currentWorkSet.add(func)
        # noinspection PyUnresolvedReferences
        currentWorkSet.save()
        workerQueue.put(func)
        # noinspection PyUnresolvedReferences
        workerQueue.save()
        workerQueueSet.add(func)


def reached_suggested_max_queue():
    return len(currentWorkSet) >= kSuggestedMaxQueuedActions


def main_loop():
    """
    We assume this runs in the main-thread.
    """
    while True:
        func = mainLoopQueue.get()
        func()


def watcher_loop():
    import main
    import Action
    better_exchook.install()

    while not exitEvent.isSet():
        if main.DownloadOnly:
            if len(currentWorkSet) == 0:
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


class WorkerThread(Thread):
    def __init__(self, idx):
        """
        :param int idx:
        """
        super(WorkerThread, self).__init__(name="Worker %i/%i" % (idx + 1, kNumWorkers))
        self.idx = idx
        self.daemon = True
        self.cur_item = None
        self.lock = Lock()

    def run(self):
        better_exchook.install()
        while True:
            with lock:
                func = workerQueue.get()
                if func in workerQueueSet:
                    workerQueueSet.remove(func)
            Logging.log("Next work item: %s" % func, "remaining: %i" % workerQueue.qsize())
            with self.lock:
                self.cur_item = func
            try:
                func()
            except SystemExit:
                return
            except Exception:
                Logging.log_exception("Worker", *sys.exc_info())
            finally:
                # Note: func() can add itself back to the work-queue.
                with lock:
                    if func not in workerQueueSet:
                        if func in currentWorkSet:
                            currentWorkSet.remove(func)
                            # noinspection PyUnresolvedReferences
                            currentWorkSet.save()

    def __str__(self):
        with self.lock:
            return "%s, %s" % (self.name, self.cur_item)


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
    missing_work = currentWorkSet - current_work_real
    for func in missing_work:
        workerQueue.put(func)
    # Fixup current work set.
    currentWorkSet.update(current_work_real)
    workerQueueSet.update(currentWorkSet)
    # Now init the threads.
    for i in range(kNumWorkers - len(workers)):
        thread = WorkerThread(idx=i)
        workers.append(thread)
        thread.start()


def _init_watcher_thread():
    global watcher
    if watcher:
        return
    watcher = Thread(target=watcher_loop, name="Watcher")
    watcher.daemon = True
    watcher.start()



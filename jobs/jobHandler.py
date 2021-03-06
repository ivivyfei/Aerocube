from collections import deque

from logger import Logger
from .aeroCubeJob import AeroCubeJob
from .aeroCubeSignal import *
from .settings import job_id_bundle_key

logger = Logger('jobHandler.py', active=True, external=True)


class JobHandler(object):
    """
    Handles incoming events in a queue, providing methods to peek at events and
    properly resolve/dequeue them.
    Raises a TypeError if an object that is not an AeroCubeEvent is Attempted
    to be enqueued.
    For all other operations, JobHandler will return None if an operation is
    improperly used (e.g., if dequeue_event is called on an JobHandler with
    no events).
    :ivar _job_deque: queue-style structure that stores incoming events
    :ivar _on_start_event: function handler for "on_start_event"
    :ivar _on_job_enqueue: function handler for "on_enqueue"
    :ivar _on_job_dequeue: function handler for "on_dequeue"
    :ivar _state: state chosen from inner class State that controls how incoming events are dealt with
    """

    # TODO: Structure for Event Priorities

    class NotAllowedInStateException(Exception):
        """
        NotAllowedInStateException is thrown when a function is called that is not permitted in the current JobHandler
        state
        """
        def __init__(self, message):
            super(JobHandler.NotAllowedInStateException, self).__init__(message)

    class State(Enum):
        # Ready to receive & start events
        STARTED                     = 0x0000aaaa
        # Waiting for results
        PENDING                     = 0x0000bbbb
        # Paused
        STOPPED                     = 0x0000cccc
        # Will Stop After Current Event Resolved
        PENDING_STOP_ON_RESOLVE     = 0x0000dddd

    def __init__(self, start_event_observer=None, job_enqueue_observer=None, job_dequeue_observer=None):
        self._job_deque = deque()
        self._on_start_event = start_event_observer
        self._on_job_enqueue = job_enqueue_observer
        self._on_job_dequeue = job_dequeue_observer
        self._state = JobHandler.State.STARTED

    # setters for function handlers

    def set_start_event_observer(self, observer):
        """
        Set a function to be called when start_event is run
        :param observer: a function with parameter event, the event that is started
        """
        self._on_start_event = observer
        logger.debug(
            self.__class__.__name__,
            func_name='set_start_event_observer',
            msg='Set on_start_event',
            id=None)

    def set_job_enqueue_observer(self, observer):
        """
        Set a function to be called when a job is enqueued
        :param observer: a function with parameter job, the job that is enqueued
        """
        self._on_job_enqueue = observer
        logger.debug(
            self.__class__.__name__,
            func_name='set_job_enqueue_observer',
            msg='Set on_job_enqueue',
            id=None)

    def set_job_dequeue_observer(self, observer):
        """
        Set a function to be called when a job is dequeued
        :param observer: a function with parameter job, the job that is dequeued
        """
        self._on_job_dequeue = observer
        logger.debug(
            self.__class__.__name__,
            func_name='set_job_dequeue_observer',
            msg='Set on_job_dequeue',
            id=None)

    # getter functions or functions to allow observation of the internal event deque

    def enqueue_job(self, job):
        """
        Adds a new job
        :param job: the new job to be added
        :return:
        """
        logger.debug(
            self.__class__.__name__,
            func_name='enqueue_job',
            msg='Enqueued job: \r\n{}\r\n'.format(job),
            id=job.uuid)
        if JobHandler.is_valid_element(job):
            self._job_deque.append(job)
        else:
            raise TypeError("Attempted to queue invalid object to JobHandler")
        # Try to restart the sending process on enqueue
        try:
            if self._on_job_enqueue is not None:
                self._on_job_enqueue(job)
            if self._state == JobHandler.State.STARTED or self._state == JobHandler.State.STOPPED:
                self._state = JobHandler.State.STARTED
                self._start_sending_events()
            elif self._state == JobHandler.State.PENDING or self._state == JobHandler.State.PENDING_STOP_ON_RESOLVE:
                pass
        except JobHandler.NotAllowedInStateException as e:
            logger.err(
                self.__class__.__name__,
                func_name='enqueue_job',
                msg=e,
                id=job.uuid)

    @property
    def state(self):
        """
        Get the state of the JobHandler
        :return: The state of the JobHandler
        """
        return self._state

    @property
    def has_jobs(self):
        """
        Check if there are any events
        :return: true if there are events
        """
        return len(self._job_deque) > 0

    def _dequeue_job(self):
        """
        Dequeues the current job, attempts to call on_dequeue
        :return:
        """
        dequeued_job = self._job_deque.popleft()
        if self._on_job_dequeue is not None:
            self._on_job_dequeue(dequeued_job)
        return dequeued_job

    def _peek_current_event(self):
        """
        Peeks at the current event of the current job
        :return: the current event
        """
        if self.has_jobs:
            return self._job_deque[0].current_event
        else:
            return None

    def _peek_current_job(self):
        """
        Peeks at the current job
        :return: the current job
        """
        return self._job_deque[0]

    def _peek_last_added_job(self):
        """
        Peeks at the most recently added job
        :return: the most recently added job
        """
        if self.has_jobs:
            return self._job_deque[-1]
        else:
            return None

    # state-change functions

    def restart(self):
        """
        Attempts to put the JobHandler in a STARTED state from STOPPED
        Precondition: State is STOPPED
        :return: True if successful, False if not
        """
        if self._state == JobHandler.State.STOPPED:
            self._state = JobHandler.State.STARTED
            self._start_sending_events()
            return True
        return False

    def _start_sending_events(self):
        """
        Attempts to send the first event in the queue
        Precondition: State is STARTED
        """
        if self._state != JobHandler.State.STARTED:
            raise JobHandler.NotAllowedInStateException('ERROR: JobHandler must be in STARTED state to send events')
        if self.has_jobs:
            self._start_event()

    def _continue_sending_events(self):
        """
        Attempts
        Precondition: State is PENDING
        """
        if self._state != JobHandler.State.PENDING:
            raise JobHandler.NotAllowedInStateException('ERROR: JobHandler must be in PENDING state to continue sending events')
        self._state = JobHandler.State.STARTED
        logger.debug(
            self.__class__.__name__,
            '_continue_sending_events',
            msg='State changed to {}'.format(self._state),
            id=None)
        self._start_sending_events()

    def _resolve_state(self):
        """
        Precondition: State is PENDING or PENDING_STOP_ON_RESOLVE
        """
        if self._state == JobHandler.State.PENDING:
            self._continue_sending_events()
        elif self._state == JobHandler.State.PENDING_STOP_ON_RESOLVE:
            self._state = JobHandler.State.STOPPED
            logger.debug(
                self.__class__.__name__,
                '_resolve_state',
                msg='State changed to {}'.format(self._state),
                id=None)
        else:
            raise JobHandler.NotAllowedInStateException('ERROR: JobHandler must be in PENDING or PENDING_STOP_ON_RESOLVE to resolve current event')

    def stop(self):
        """
        Attempts to put the JobHandler in a STOPPED state, waiting until the currently pending event is resolved
        :return: True if successfully directs the JobHandler to switch to a STOPPED state, either then or
        after the current event is resolved. False otherwise.
        """
        if self._state == JobHandler.State.PENDING:
            self._state = JobHandler.State.PENDING_STOP_ON_RESOLVE
            logger.debug(
                self.__class__.__name__,
                'stop',
                msg='State changed to {}'.format(self._state),
                id=None)
        elif self._state == JobHandler.State.STARTED:
            self._state = JobHandler.State.STOPPED
            logger.debug(
                self.__class__.__name__,
                'stop',
                msg='State changed to {}'.format(self._state),
                id=None)
        else:
            return False
        return True

    def force_stop(self):
        """
        Forces the JobHandler into a STOPPED state. Note, calling resolve_event will trigger an error while the
        JobHandler is in a STOPPED state. If an attempt to resolve the event is dropped, upon re-starting
        :return:
        """
        logger.debug(
            self.__class__.__name__,
            'force_stop',
            msg='Force Stop Triggered',
            id=None)
        self._state = JobHandler.State.STOPPED
        logger.warn(
            self.__class__.__name__,
            'force_stop',
            msg='State changed to {}'.format(self._state),
            id=None)

    def resolve_event(self, event):
        """
        Logic to resolve "finished" events/jobs in the JobHandler deque could
        either be handled within this class, or lie in the calling class.
        Needs to be determined.
        :return: if event is resolved/finished, return true; else, return false
        """
        if self._can_state_resolve():
            # Modify JobHandler queue (assuming state is valid)
            self._peek_current_job().update_current_node(event, merge_payload=True)
            logger.success(
                self.__class__.__name__,
                'resolve_event',
                msg='Resolved Event: \r\n{}\r\n'.format(event),
                id=event.payload.strings(job_id_bundle_key))
            # Check if the job is finished
            if self._peek_current_job().is_finished:
                self._dequeue_job()

            # Update state
            self._resolve_state()
            logger.debug(
                self.__class__.__name__,
                'resolve_event',
                msg='State changed to {}'.format(self._state),
                id=event.payload.strings(job_id_bundle_key))
            return True
        else:
            # Do not modify JobHandler state or queue, but log ResultEvent
            logger.warn(
                self.__class__.__name__,
                'resolve_event',
                msg='ResultEvent (not resolved): \r\n{}\r\n'.format(event),
                id=event.payload.strings(job_id_bundle_key))
            # Return False to indicate calling_event not finished
            return False

    def _can_state_resolve(self):
        # Check if state is valid
        if self._state == JobHandler.State.STARTED:
            # Raise Error
            raise JobHandler.NotAllowedInStateException('ERROR: Attempted to resolve event while not pending for a result')
        elif self._state == JobHandler.State.STOPPED:
            # Raise Error
            raise JobHandler.NotAllowedInStateException('ERROR: Attempted to resolve event while stopped')
        return True

    def _start_event(self):
        """
        Start an event of the current job by calling the on_start_event function and passing it the first event in the queue.
        This action puts the JobHandler in a PENDING state.
        Preconditions: state must be STARTED; on_start_event must be not None
        :raises NotImplementedError if on_start_event is not defined
        """
        if self._state != JobHandler.State.STARTED:
            raise JobHandler.NotAllowedInStateException('ERROR: Attempted to start event while not in STARTED state')
        if self._on_start_event is not None:
            logger.debug(
                self.__class__.__name__,
                '_start_event',
                msg='Starting event: \r\n{}\r\n'.format(self._peek_current_event()),
                id=None)
            self._state = JobHandler.State.PENDING
            self._on_start_event(self, self._peek_current_event())
            logger.debug(
                self.__class__.__name__,
                '_start_event',
                msg='State changed to {}'.format(self._state),
                id=None)
        else:
            raise NotImplementedError('ERROR: Must call set_start_event_observer before an event can be sent')

    # static helper function(s)

    @staticmethod
    def is_valid_element(obj):
        """
        Check if the obj is an instance of AeroCubeJob
        :param obj:
        :return:
        """
        return isinstance(obj, AeroCubeJob)

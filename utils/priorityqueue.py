class PriorityItem:
    def __init__(self, item, priority=0):
        if priority < 0:
            raise ValueError("Priority < 0")
        elif priority > MAX_PRIORITY:
            raise ValueError("Priority > MAX_PRIORTY")
        self.priority = priority
        self.item = item

    def __str__(self):
        return str(self.item)

    def __repr__(self):
        return self.__str__()


def _get_prior(prio: PriorityItem):
    return prio.priority


MAX_PRIORITY = 1000


class PriorityQueue:

    def __init__(self):
        self._internal_queue = []

    def push(self, item, priority=0):
        self._internal_queue.append(PriorityItem(item, priority))
        self._internal_queue.sort(key=_get_prior, reverse=True)

    def dequeue(self):
        if len(self._internal_queue) == 0:
            return None
        item = self._internal_queue[0]
        del self._internal_queue[0]
        self._internal_queue.sort(key=_get_prior, reverse=True)
        return item.item

    def clear(self, under_priority=MAX_PRIORITY):
        l = list(filter(lambda d: d.priority < under_priority, self._internal_queue))
        for e in l:
            self._internal_queue.remove(e)
        return l

    def __len__(self):
        return len(self._internal_queue)

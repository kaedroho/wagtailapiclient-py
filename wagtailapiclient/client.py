import requests


class Object(object):
    ENDPOINT_NAME = 'unknown'

    def __init__(self, connection, data, is_detail=False):
        self.connection = connection
        self.data = data
        self.is_detail = is_detail

    def __getattr__(self, key):
        if key not in self.data and not self.is_detail:
            self.data = self.connection.get('%s/%d/' % (self.ENDPOINT_NAME, self.id))
            self.is_detail = True

        data = self.data[key]

        if isinstance(data, dict):
            if 'meta' in data:
                type_ = data['meta']['type']

                if type_ in self.connection.TYPES:
                    return self.connection.TYPES[type_](self.connection, data)

        return data

    def __repr__(self):
        return "<%s: %s>" % (self.meta['type'], self.title)


class QuerySet(object):
    def __init__(self, connection):
        self.connection = connection
        self.start = 0
        self.stop = None
        self._results_cache = None
        self._filters = {}
        self._order = ()

    def _clone(self):
        cls = self.__class__
        new = cls(self.connection)
        new.start = self.start
        new.stop = self.stop
        new._filters = self._filters.copy()
        new._order = self._order
        return new

    def _set_limits(self, start=None, stop=None):
        if stop is not None:
            if self.stop is not None:
                self.stop = min(self.stop, self.start + stop)
            else:
                self.stop = self.start + stop

        if start is not None:
            if self.stop is not None:
                self.start = min(self.stop, self.start + start)
            else:
                self.start = self.start + start

    def __getitem__(self, key):
        new = self._clone()

        if isinstance(key, slice):
            # Set limits
            start = int(key.start) if key.start else None
            stop = int(key.stop) if key.stop else None
            new._set_limits(start, stop)

            return new
        else:
            new.start = key
            new.stop = key + 1
            return list(new)[0]

    def results(self):
        if self._results_cache is None:
            self._results_cache = self.fetch_results()

        return self._results_cache

    def filter(self, **filters):
        new = self._clone()
        new._filters.update(filters)
        return new

    def get(self, **filters):
        return self.filter(**filters)[0]

    def order_by(self, *order):
        new = self._clone()
        new._order = tuple(order)
        return new

    def __iter__(self):
        return iter(self.results())

    def __len__(self):
        return len(self.results())

    def __repr__(self):
        data = list(self[:11])
        if len(data) > 10:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)


class Page(Object):
    ENDPOINT_NAME = 'pages'

    def get_parent(self):
        pass

    def get_children(self):
        return self.connection.pages.child_of(self)

    def get_siblings(self):
        return self.get_parent().get_children().exclude(id=self.id)


class Image(Object):
    ENDPOINT_NAME = 'images'


class PageQuerySet(QuerySet):
    def __init__(self, connection):
        super().__init__(connection)
        self._child_of = None

    def _clone(self):
        new = super()._clone()
        new._child_of = self._child_of
        return new

    def child_of(self, page):
        new = self._clone()
        new._child_of = page.id
        return new

    def fetch_results(self):
        offset = self.start
        limit = None

        if self.stop:
            limit = self.stop - self.start

        query = []

        if limit:
            query.append('limit=%d' % limit)

        if offset:
            query.append('offset=%d' % offset)

        if self._order:
            query.append('order=%s' % ','.join(self._order))

        if self._child_of:
            query.append('child_of=%d' % self._child_of)

        for name, value in self._filters.items():
            query.append('%s=%s' % (name, str(value)))

        pages = self.connection.get('pages/?%s' % '&'.join(query))['pages']

        return [Page(self.connection, page) for page in pages]


class ImageQuerySet(QuerySet):
    def fetch_results(self):
        offset = self.start
        limit = None

        if self.stop:
            limit = self.stop - self.start

        query = []

        if limit:
            query.append('limit=%d' % limit)

        if offset:
            query.append('offset=%d' % offset)

        images = self.connection.get('images/?%s' % '&'.join(query))['images']

        return [Image(self.connection, image) for image in images]


class Connection(object):
    TYPES = {
        'wagtailimages.Image': Image,
    }

    def __init__(self, url):
        self.url = url

    def get(self, path):
        return requests.get(self.url + path).json()

    @property
    def pages(self):
        return PageQuerySet(self)

    @property
    def images(self):
        return ImageQuerySet(self)


con = Connection('http://wagtailapi.kaed.uk/api/v1/')

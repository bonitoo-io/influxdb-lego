from datetime import datetime

from pytz import UTC

DEFAULT_WRITE_PRECISION = "ns"

EPOCH = UTC.localize(datetime.utcfromtimestamp(0))


_ESCAPE_MEASUREMENT = str.maketrans({
    ',': r'\,',
    ' ': r'\ ',
    '\n': r'\n',
    '\t': r'\t',
    '\r': r'\r',
})

_ESCAPE_KEY = str.maketrans({
    ',': r'\,',
    '=': r'\=',
    ' ': r'\ ',
    '\n': r'\n',
    '\t': r'\t',
    '\r': r'\r',
})

_ESCAPE_STRING = str.maketrans({
    '"': r'\"',
    '\\': r'\\',
})


class Point(object):
    """
    Point defines the values that will be written to the database.

    Ref: http://bit.ly/influxdata-point
    """

    @staticmethod
    def measurement(measurement):
        """Create a new Point with specified measurement name."""
        p = Point(measurement)
        return p

    @staticmethod
    def from_dict(dictionary: dict, write_precision: str = "ns", **kwargs):
        """
        Initialize point from 'dict' structure.

        The expected dict structure is:
            - measurement
            - tags
            - fields
            - time

        Example:
            .. code-block:: python

                # Use default dictionary structure
                dict_structure = {
                    "measurement": "h2o_feet",
                    "tags": {"location": "coyote_creek"},
                    "fields": {"water_level": 1.0},
                    "time": 1
                }
                point = Point.from_dict(dict_structure, WritePrecision.NS)

        Example:
            .. code-block:: python

                # Use custom dictionary structure
                dictionary = {
                    "name": "sensor_pt859",
                    "location": "warehouse_125",
                    "version": "2021.06.05.5874",
                    "pressure": 125,
                    "temperature": 10,
                    "created": 1632208639,
                }
                point = Point.from_dict(dictionary,
                                        write_precision=WritePrecision.S,
                                        record_measurement_key="name",
                                        record_time_key="created",
                                        record_tag_keys=["location", "version"],
                                        record_field_keys=["pressure", "temperature"])

        :param dictionary: dictionary for serialize into data Point
        :param write_precision: sets the precision for the supplied time values
        :key record_measurement_key: key of dictionary with specified measurement
        :key record_measurement_name: static measurement name for data Point
        :key record_time_key: key of dictionary with specified timestamp
        :key record_tag_keys: list of dictionary keys to use as a tag
        :key record_field_keys: list of dictionary keys to use as a field
        :return: new data point
        """
        measurement_ = kwargs.get('record_measurement_name', None)
        if measurement_ is None:
            measurement_ = dictionary[kwargs.get('record_measurement_key', 'measurement')]
        point = Point(measurement_)

        record_tag_keys = kwargs.get('record_tag_keys', None)
        if record_tag_keys is not None:
            for tag_key in record_tag_keys:
                if tag_key in dictionary:
                    point.tag(tag_key, dictionary[tag_key])
        elif 'tags' in dictionary:
            for tag_key, tag_value in dictionary['tags'].items():
                point.tag(tag_key, tag_value)

        record_field_keys = kwargs.get('record_field_keys', None)
        if record_field_keys is not None:
            for field_key in record_field_keys:
                if field_key in dictionary:
                    point.field(field_key, dictionary[field_key])
        else:
            for field_key, field_value in dictionary['fields'].items():
                point.field(field_key, field_value)

        record_time_key = kwargs.get('record_time_key', 'time')
        if record_time_key in dictionary:
            point.time(dictionary[record_time_key], write_precision=write_precision)
        return point

    def __init__(self, measurement_name):
        """Initialize defaults."""
        self._tags = {}
        self._fields = {}
        self._name = measurement_name
        self._time = None
        self._write_precision = DEFAULT_WRITE_PRECISION
        pass

    def time(self, time, write_precision=DEFAULT_WRITE_PRECISION):
        """
        Specify timestamp for DataPoint with declared precision.

        If time doesn't have specified timezone we assume that timezone is UTC.

        Examples::
            Point.measurement("h2o").field("val", 1).time("2009-11-10T23:00:00.123456Z")
            Point.measurement("h2o").field("val", 1).time(1257894000123456000)
            Point.measurement("h2o").field("val", 1).time(datetime(2009, 11, 10, 23, 0, 0, 123456))
            Point.measurement("h2o").field("val", 1).time(1257894000123456000, write_precision=WritePrecision.NS)


        :param time: the timestamp for your data
        :param write_precision: sets the precision for the supplied time values
        :return: this point
        """
        self._write_precision = write_precision
        self._time = time
        return self

    def tag(self, key, value):
        """Add tag with key and value."""
        self._tags[key] = value
        return self

    def field(self, field, value):
        """Add field with key and value."""
        self._fields[field] = value
        return self

    def to_line_protocol(self):
        """Create LineProtocol."""
        _measurement = _escape_key(self._name, _ESCAPE_MEASUREMENT)
        _tags = _append_tags(self._tags)
        _fields = _append_fields(self._fields)
        if not _fields:
            return ""
        _time = _append_time(self._time, self._write_precision)

        return f"{_measurement}{_tags}{_fields}{_time}"

    @property
    def write_precision(self):
        """Get precision."""
        return self._write_precision


def _append_tags(tags):
    _return = []
    for tag_key, tag_value in sorted(iteritems(tags)):

        if tag_value is None:
            continue

        tag = _escape_key(tag_key)
        value = _escape_tag_value(tag_value)
        if tag != '' and value != '':
            _return.append(f'{tag}={value}')

    return f"{',' if _return else ''}{','.join(_return)} "


def _append_fields(fields):
    _return = []

    for field, value in sorted(iteritems(fields)):
        if value is None:
            continue

        if isinstance(value, float) or isinstance(value, Decimal) or _np_is_subtype(value, 'float'):
            if not math.isfinite(value):
                continue
            s = str(value)
            # It's common to represent whole numbers as floats
            # and the trailing ".0" that Python produces is unnecessary
            # in line-protocol, inconsistent with other line-protocol encoders,
            # and takes more space than needed, so trim it off.
            if s.endswith('.0'):
                s = s[:-2]
            _return.append(f'{_escape_key(field)}={s}')
        elif (isinstance(value, int) or _np_is_subtype(value, 'int')) and not isinstance(value, bool):
            _return.append(f'{_escape_key(field)}={str(value)}i')
        elif isinstance(value, bool):
            _return.append(f'{_escape_key(field)}={str(value).lower()}')
        elif isinstance(value, str):
            _return.append(f'{_escape_key(field)}="{_escape_string(value)}"')
        else:
            raise ValueError(f'Type: "{type(value)}" of field: "{field}" is not supported.')

    return f"{','.join(_return)}"


def _append_time(time, write_precision):
    if time is None:
        return ''
    return f" {int(_convert_timestamp(time, write_precision))}"


def _escape_key(tag, escape_list=None):
    if escape_list is None:
        escape_list = _ESCAPE_KEY
    return str(tag).translate(escape_list)


def _escape_tag_value(value):
    ret = _escape_key(value)
    if ret.endswith('\\'):
        ret += ' '
    return ret


def _escape_string(value):
    return str(value).translate(_ESCAPE_STRING)


def _convert_timestamp(timestamp, precision=DEFAULT_WRITE_PRECISION):
    date_helper = get_date_helper()
    if isinstance(timestamp, Integral):
        return timestamp  # assume precision is correct if timestamp is int

    if isinstance(timestamp, str):
        timestamp = date_helper.parse_date(timestamp)

    if isinstance(timestamp, timedelta) or isinstance(timestamp, datetime):

        if isinstance(timestamp, datetime):
            timestamp = date_helper.to_utc(timestamp) - EPOCH

        ns = date_helper.to_nanoseconds(timestamp)

        if precision is None or precision == WritePrecision.NS:
            return ns
        elif precision == WritePrecision.US:
            return ns / 1e3
        elif precision == WritePrecision.MS:
            return ns / 1e6
        elif precision == WritePrecision.S:
            return ns / 1e9

    raise ValueError(timestamp)


def _np_is_subtype(value, np_type):
    if not _HAS_NUMPY or not hasattr(value, 'dtype'):
        return False

    if np_type == 'float':
        return np.issubdtype(value, np.floating)
    elif np_type == 'int':
        return np.issubdtype(value, np.integer)
    return False

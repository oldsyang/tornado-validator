"""Module that provides the default converters and converter registry.
Converters will be auto registered in the ConverterRegistry
If you haven't specify the name attribute in Meta
class, registry will auto use the class name.
Example:
    class ConverterExample(BaseConverter):
        @staticmethod
        def convert(key, string):
            pass
        class Meta:
            name = ('example', )
But if you can't auto import the converter
class, you can register the converter manually.
Example:
    ConverterExample.register()
    ConverterExample.register('example')
"""
import re
from datetime import datetime

from .validators import BaseRegexValidator, IntegerValidator, NumericValidator

try:
    from gettext import gettext, ngettext
except ImportError:
    def gettext(message):
        return message

    def ngettext(singular, plural, n):
        if n == 1:
            return singular
        return plural

_ = gettext


class ConverterRegistry(object):
    """
    Registry for all converters.
    """
    _registry = {}

    @classmethod
    def register(cls, name, _class):
        """Register Converter in ConverterRegistry.
        Args:
            name (str, iterable): Register key or name tuple.
            _class (BaseConverter): Converter class.
        """
        if isinstance(name, (tuple, set, list)):
            for _name in name:
                cls._registry[_name] = _class
        else:
            cls._registry[name] = _class

    @classmethod
    def get(cls, name):
        return cls._registry.get(name, StringConverter)


class ConverterMetaClass(type):
    """
    Metaclass for all Converters.
    """

    def __new__(cls, name, bases, attributes):
        _class = super(
            ConverterMetaClass,
            cls).__new__(
            cls,
            name,
            bases,
            attributes)
        attr_meta = attributes.pop('Meta', None)
        abstract = getattr(attr_meta, 'abstract', False)
        if not abstract:
            _class.register()

        return _class


class BaseConverter(metaclass=ConverterMetaClass):
    """
    Abstract super class for all converters.
    """

    @staticmethod
    def convert(key, string):
        raise NotImplementedError

    @classmethod
    def register(cls, name=None):
        """Register this converter to registry.
        Attributes:
            name (Optinal[str, iterable]): Name that used to
                register in registry.
                Defaults to the name in Meta class.
        """
        if name is None:
            attr_meta = getattr(cls, 'Meta', None)
            name = getattr(attr_meta, 'name', cls.__name__)
        ConverterRegistry.register(name, cls)

    class Meta:
        """Meta class of Converter
        Attributes:
            abstract (bool): Class will not auto register
                            if this attribute is True.
            name (Optional[str, iterable]): Name that used
            to auto register in registry.
        """
        abstract = True


class StringConverter(BaseConverter):
    """
    Converter that just passing the value.
    """

    @staticmethod
    def convert(key, string):
        if string is None:
            return None
        return str(string)

    class Meta:
        name = ('string', 'str')


class IntegerConverter(BaseConverter):
    """
    Convert the value to an integer value.
    """
    integer_validator = IntegerValidator()

    @staticmethod
    def convert(key, string):
        if string is None:
            return None
        IntegerConverter.integer_validator(key, {key: string})
        return int(string)

    class Meta:
        name = ('integer', 'int')


class FloatConverter(BaseConverter):
    """
    Convert the value to a float value.
    """
    numeric_validator = NumericValidator()

    @staticmethod
    def convert(key, string):
        if string is None:
            return None
        FloatConverter.numeric_validator(key, {key: string})
        return float(string)

    class Meta:
        name = 'float'


class BooleanConverter(BaseConverter):
    """
    Convert the value to a boolean value.
    """

    # Set is the faster than tuple and list, but False is equals 0 in set
    # structure.
    false_values = {None, False, 'false', 'False', 0, '0'}

    @staticmethod
    def convert(key, string):
        return string not in BooleanConverter.false_values

    class Meta:
        name = ('boolean', 'bool')


class FileConverter(BaseConverter):
    """
    Pass the file object.
    """

    @staticmethod
    def convert(key, value):
        return value

    class Meta:
        name = ('file',)


class DateValidator(BaseRegexValidator):
    """
    Inherit regex validator to confirm numbers.
    """
    code = 'numeric_validator'
    message = _('The {key} must be a yyyy-MM-dd or yyyy-M-d.')
    regex = re.compile('(\\d{4}-\\d{1,2}-\\d{1,2})')

    def __init__(self, message=None):
        super(DateValidator, self).__init__(message)

    def is_valid(self, value, params):
        if self.regex.match(value):
            try:
                datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return False
            return True
        return False


class DateConverter(BaseConverter):
    """
    Pass the date parameter.
    """
    date_validator = DateValidator()

    @staticmethod
    def convert(key, value):
        if value is None:
            return None
        DateConverter.date_validator(key, {key: value})
        return datetime.strptime(value, '%Y-%m-%d').date()

    class Meta:
        name = ('date',)

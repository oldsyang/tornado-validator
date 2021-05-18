import json
from functools import partial, wraps

from .converters import ConverterRegistry
from .exceptions import ValidationError
from .validators import ValidatorRegistry


def get_body(request):
    post_data = {x: vals[0].decode("utf-8") for x, vals in request.body_arguments.items()}
    if not post_data:
        post_data = request.body.decode('utf-8')
        post_data = json.loads(post_data) if post_data else dict()

    return post_data


def _get_lookup(_decorator, request, name, default, kwargs):
    return request.get_query_argument(name, default)


def _post_lookup(_decorator, request, name, default, kwargs):
    body_data = getattr(_decorator, "_val_body_data", None)
    if not body_data:
        _decorator._val_body_data = body_data = get_body(request.request)

    return body_data.get(name, default)


def _file_lookup(_decorator, request, name, default, kwargs):
    _body_file = getattr(_decorator, "_val_body_file", None)
    if not _body_file:
        _decorator._val_body_file = _body_file = request.request.files

    return _body_file.get(name, default)  # 获取上传文件信息


def _post_or_get_lookup(_decorator, request, name, default, kwargs):
    value = _post_lookup(_decorator, request, name, None, kwargs)
    return value if value is not None else _get_lookup(_decorator, request, name, default, kwargs)


def _header_lookup(_decorator, request, name, default, kwargs):
    _headers = getattr(_decorator, "_val_headers", {})
    if not _headers:
        _decorator._val_headers = _headers = request.request.headers

    return _headers.get(name, default)


def _uri_lookup(_decorator, request, name, default, kwargs):
    return kwargs.get(name, default)


def param(name, related_name=None, verbose_name=None, default=None, type='string', lookup=_get_lookup, many=False,
          separator=',', validators=None, validator_classes=None):
    return _Param(name, related_name, verbose_name, default, type, lookup, many, separator, validators,
                  validator_classes)


class _Param(object):
    def __init__(self, name, related_name, verbose_name, default, type, lookup, many, separator, validators,
                 validator_classes):
        self.name = name
        self.related_name = related_name if related_name else name
        self.verbose_name = verbose_name if verbose_name else name
        self.default = default
        self.type = type
        self.lookup = lookup
        self.many = many
        self.separator = separator
        self.validators = ValidatorRegistry.get_validators(validators)
        if validator_classes:
            if hasattr(validator_classes, '__iter__'):
                self.validators.extend(validator_classes)
            else:
                self.validators.append(validator_classes)

    def __call__(self, func):
        if hasattr(func, '__params__'):
            func.__params__.append(self)
            return func

        @wraps(func)
        def _decorator(*args, **kwargs):
            if len(args) < 1:
                # Call function immediately, maybe raise an error is better.
                return func(*args, **kwargs)

            request = args[0]

            if request:
                # Checkout all the params first.
                for _param in _decorator.__params__:
                    _param._parse(_decorator, request, kwargs)
                # Validate after all the params has checked out, because some validators needs all the params.
                for _param in _decorator.__params__:
                    for validator in _param.validators:
                        validator(_param.related_name, kwargs, _param.verbose_name)

                for _val in ['_val_body_data', '_val_body_file', '_val_headers']:
                    try:
                        delattr(_decorator, _val)
                    except Exception as e:
                        pass
                return func(*args, **kwargs)

        _decorator.__params__ = [self]
        return _decorator

    def _parse(self, _decorator, request, kwargs):
        converter = ConverterRegistry.get(self.type)
        value = self.lookup(_decorator, request, self.name, self.default, kwargs)
        try:
            if self.many:
                if isinstance(value, str):
                    values = value.split(self.separator)
                elif value is None:
                    values = []
                else:
                    values = value
                converted_value = [converter.convert(self.name, _value) for _value in values]
            else:
                converted_value = converter.convert(self.name, value)
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError('Type Convert error: %s' % e.message)

        kwargs[self.related_name] = converted_value


GET = partial(param, lookup=_get_lookup)
POST = partial(param, lookup=_post_lookup)
FILE = partial(param, type='file', lookup=_file_lookup)
POST_OR_GET = partial(param, lookup=_post_or_get_lookup)
HEADER = partial(param, lookup=_header_lookup)
URI = partial(param, lookup=_uri_lookup)

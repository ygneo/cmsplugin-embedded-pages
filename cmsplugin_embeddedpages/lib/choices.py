import os
import logging
from django.db.utils import DatabaseError
from django.template.loader import get_template
from django.template.loaders.app_directories import app_template_dirs
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module


logger = logging.getLogger(__name__)

try:
  from cms.models import Placeholder, Page
except ImportError, error:
  pass

from .formatting import deslugify

class DynamicChoice(object):
    """
    Trivial example of creating a dynamic choice
    """

    def __iter__(self, *args, **kwargs):
        try:
            for choice in self.generate():
                if hasattr(choice,'__iter__'):
                    yield (choice[0], choice[1])
                else:
                    yield choice, choice

        except DatabaseError, error:
            logger.exception(error)


    def __init__(self, *args, **kwargs):
        """
        If you do it here it is only initialized once. Then just return generated.
        """
        pass

    def generate(self, *args, **kwargs):
        """
        If you do it here it is  initialized every time the iterator is used.
        """
        pass


class PageAttributeDynamicChoices(DynamicChoice):

    def __init__(self, *args, **kwargs):
        super(PageAttributeDynamicChoices, self).__init__(self, *args, **kwargs)

    def generate(self,*args, **kwargs):
        choices = list()
        return choices


class PlaceholdersDynamicChoices(DynamicChoice):

    def __init__(self, *args, **kwargs):
        super(PlaceholdersDynamicChoices, self).__init__(self, *args, **kwargs)

    def generate(self,*args, **kwargs):
        choices = list()
        for item in Placeholder.objects.all().values("slot").distinct():
            choices += ((
              item['slot'],
              deslugify(item['slot'])
              ), )

        return choices

class PageIDsDynamicChoices(DynamicChoice):

    def __init__(self, *args, **kwargs):
        super(PageIDsDynamicChoices, self).__init__(self, *args, **kwargs)

    def generate(self,*args, **kwargs):
        choices = list()
        try:
            pages = Page.objects.all()

            for item in pages:
                if not item.reverse_id :
                    continue

                choices += ((
                  item.reverse_id,
                  "{0} [{1}]".format(item.get_title(), item.reverse_id)
                  ), )

        except Exception, error:
            pass

        return choices


class DynamicTemplateChoices(DynamicChoice):

    def __init__(self, path=None, include=None,
                       exclude=None, *args, **kwargs):

        super(DynamicTemplateChoices, self).__init__(self, *args, **kwargs)
        self.path = path
        self.include = include
        self.exlude = exclude

    def generate(self,*args, **kwargs):
        choices = set()
        for template_dir in app_template_dirs + settings.TEMPLATE_DIRS:
          choices |= set(self.walkdir(os.path.join(template_dir, self.path)))
        return choices

    def walkdir(self, path=None):

        if not os.path.exists(path):
            return

        for root, dirs, files in os.walk(path):

            if self.include:
                files = filter(lambda x: self.include in x, files)

            if self.exlude:
                files = filter(lambda x: not self.exlude in x, files)

            for item in files :
                fragment = os.path.relpath(os.path.join(root, item), path)
                yield (
                    os.path.join(self.path, fragment),
                    deslugify(os.path.splitext(item)[0]),
                )

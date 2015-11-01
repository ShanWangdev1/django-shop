# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.six.moves.urllib.parse import urljoin
from filer.fields import image
from filer.models import Image
from cms.models.fields import PlaceholderField
from djangocms_text_ckeditor.fields import HTMLField
from parler.models import TranslatableModel, TranslatedFieldsModel
from parler.fields import TranslatedField
from parler.managers import TranslatableManager, TranslatableQuerySet
from polymorphic.query import PolymorphicQuerySet
import reversion
from shop.models.product import BaseProductManager, BaseProduct


class ProductQuerySet(TranslatableQuerySet, PolymorphicQuerySet):
    pass


class ProductManager(BaseProductManager, TranslatableManager):
    queryset_class = ProductQuerySet

    def select_lookup(self, term):
        query = models.Q(name__icontains=term) | models.Q(slug__icontains=term)
        return self.get_queryset().filter(query)


class Product(TranslatableModel, BaseProduct):
    order = models.PositiveIntegerField(verbose_name=_("Sort by"), db_index=True)
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    slug = models.SlugField(verbose_name=_("Slug"))
    description = TranslatedField()
    images = models.ManyToManyField(Image, through='ProductImage', null=True)
    placeholder = PlaceholderField('Product Detail',
        verbose_name=_("Additional description for this product."))

    class Meta:
        app_label = settings.SHOP_APP_LABEL
        ordering = ('order',)

    objects = ProductManager()

    # filter expression used to search for a product item using the Select2 widget
    search_fields = ('identifier__istartswith', 'translations__name__istartswith',)

    def get_price(self, request):
        # TODO: fix this gross_price = self.unit_price * (1 + settings.SHOP_VALUE_ADDED_TAX / 100)
        gross_price = 0
        return gross_price

    def get_absolute_url(self):
        # sorting by highest level, so that the canonical URL associates with the most generic category
        cms_page = self.cms_pages.order_by('depth').last()
        if cms_page is None:
            return urljoin('category-not-assigned', self.slug)
        return urljoin(cms_page.get_absolute_url(), self.slug)

    @property
    def product_name(self):
        return self.name

    @property
    def product_code(self):
        return self.slug

    @property
    def sample_image(self):
        return self.images.first()

reversion.register(Product, adapter_cls=type(str('ProductVersionAdapter'), (reversion.VersionAdapter,),
                                             {'format': 'shop'}))


class ProductTranslation(TranslatedFieldsModel):
    master = models.ForeignKey(Product, related_name='translations', null=True)
    description = HTMLField(verbose_name=_("Description"),
                            help_text=_("Description for the list view of products."))

    class Meta:
        unique_together = [('language_code', 'master')]
        app_label = settings.SHOP_APP_LABEL


class ProductImage(models.Model):
    image = image.FilerImageField()
    product = models.ForeignKey(Product)
    order = models.SmallIntegerField(default=0, blank=False, null=False)

    class Meta:
        app_label = settings.SHOP_APP_LABEL
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ('order',)

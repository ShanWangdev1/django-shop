# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms import fields, widgets
from django.core.exceptions import ValidationError
from django.template import engines
from django.template.loader import select_template
from django.utils.translation import ugettext_lazy as _
from entangled.forms import EntangledModelFormMixin
from cms.plugin_pool import plugin_pool
from cmsplugin_cascade.bootstrap4.buttons import BootstrapButtonMixin
from cmsplugin_cascade.plugin_base import TransparentWrapper
from djng.forms import fields, NgModelFormMixin
from djng.styling.bootstrap3.forms import Bootstrap3Form
from shop.cascade.extensions import ShopExtendableMixin, LeftRightExtensionMixin
from shop.cascade.plugin_base import ShopPluginBase
from shop.conf import app_settings


class ShopOrderViewsForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        if self.instance.page and self.instance.page.application_urls != 'OrderApp':
            msg = "This plugin only makes sense if used on a CMS page with an application of type 'OrderApp'."
            raise ValidationError(msg)
        return cleaned_data


class ShopOrderViewsPlugin(LeftRightExtensionMixin, TransparentWrapper, ShopPluginBase):
    name = _("Order Views")
    require_parent = True
    parent_classes = ['BootstrapColumnPlugin']
    allow_children = True
    model_mixins = (ShopExtendableMixin,)
    form = ShopOrderViewsForm
    cache = False

    def get_render_template(self, context, instance, placeholder):
        many = context.get('many')
        if many is True:
            # render Order List View
            return select_template([
                '{}/order/list.html'.format(app_settings.APP_LABEL),
                'shop/order/list.html',
            ])
        if many is False:
            # render Order Detail View
            return select_template([
                '{}/order/detail.html'.format(app_settings.APP_LABEL),
                'shop/order/detail.html',
            ])
        # can happen, if this plugin is abused outside of an OrderView
        alert_msg = '''<div class="alert alert-danger">
        This {} plugin is used on a CMS page without an application of type "View Order".
        </div>'''
        return engines['django'].from_string(alert_msg.format(self.name))

plugin_pool.register_plugin(ShopOrderViewsPlugin)


class OrderButtonForm(ShopOrderViewsForm):
    button_content = fields.CharField(
        label=_("Button Content"),
        required=False,
        widget=widgets.TextInput(),
    )

    def __init__(self, raw_data=None, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            initial = {'button_content': instance.glossary.get('button_content') }
            kwargs.update(initial=initial)
        super(OrderButtonForm, self).__init__(raw_data, *args, **kwargs)

    def clean(self):
        cleaned_data = super(OrderButtonForm, self).clean()
        if self.is_valid():
            cleaned_data['glossary']['button_content'] = cleaned_data['button_content']
        return cleaned_data


class OrderButtonBase(BootstrapButtonMixin, ShopPluginBase):
    parent_classes = ['BootstrapColumnPlugin']
    form = OrderButtonForm
    fields = ['button_content', 'glossary']
    glossary_field_order = ['button_type', 'button_size', 'button_options', 'quick_float',
                            'icon_align', 'icon_font', 'symbol']

    class Media:
        css = {'all': ['cascade/css/admin/bootstrap4-buttons.css', 'cascade/css/admin/iconplugin.css']}

    @classmethod
    def get_identifier(cls, instance):
        return instance.glossary.get('button_content', '')

    def render(self, context, instance, placeholder):
        context = super(OrderButtonBase, self).render(context, instance, placeholder)
        context.update({
            'button_label': instance.glossary.get('button_content', '')
        })
        return context


class ShopReorderButtonPlugin(OrderButtonBase):
    name = _("Reorder Button")

    def get_render_template(self, context, instance, placeholder):
        template_names = [
            '{}/order/reorder-button.html'.format(app_settings.APP_LABEL),
            'shop/order/reorder-button.html',
        ]
        return select_template(template_names)

plugin_pool.register_plugin(ShopReorderButtonPlugin)


class ShopCancelOrderButtonPlugin(OrderButtonBase):
    name = _("Cancel Order Button")

    def get_render_template(self, context, instance, placeholder):
        template_names = [
            '{}/order/cancel-button.html'.format(app_settings.APP_LABEL),
            'shop/order/cancel-button.html',
        ]
        return select_template(template_names)

plugin_pool.register_plugin(ShopCancelOrderButtonPlugin)


class AddendumForm(NgModelFormMixin, Bootstrap3Form):
    annotation = fields.CharField(
        label="",
        widget=widgets.Textarea(attrs={'rows': 2}),
    )


class ShopOrderAddendumFormMixin(EntangledModelFormMixin):
    show_history = fields.BooleanField(
         label=_("Show History"),
         initial=True,
         required=False,
         help_text=_("Show historical annotations."),
    )

    class Meta:
        entangled_fields = {'glossary': ['show_history']}


class ShopOrderAddendumFormPlugin(OrderButtonBase):
    name = _("Order Addendum Form")
    form = ShopOrderAddendumFormMixin

    def get_render_template(self, context, instance, placeholder):
        template_names = [
            '{}/order/addendum-form.html'.format(app_settings.APP_LABEL),
            'shop/order/addendum-form.html',
        ]
        return select_template(template_names)

    def render(self, context, instance, placeholder):
        context = super(ShopOrderAddendumFormPlugin, self).render(context, instance, placeholder)
        context.update({
            'addendum_form': AddendumForm(),
            'show_history': instance.glossary.get('show_history', True),
        })
        return context

plugin_pool.register_plugin(ShopOrderAddendumFormPlugin)

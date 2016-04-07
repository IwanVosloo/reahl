# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Widgets and Layouts that provide an abstraction on top of Bootstrap (http://getbootstrap.com/)

.. versionadded:: 3.2

"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from copy import copy

from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance
from reahl.component.i18n import Translator

import reahl.web.ui
from reahl.web.ui import A, Article, Body, Br, Caption, Col, ColGroup, Div, FieldSet, Footer, H, Head, Header, Img, \
    Label, Li, Link, LiteralHTML, Meta, Nav, Ol, OptGroup, P, RunningOnBadge, Slot, Span, Tbody, Td, TextNode, \
    Tfoot, Th, Thead, Title, Tr, Ul, HTML5Page, DynamicColumn, StaticColumn

from reahl.web.bootstrap.grid import ColumnLayout, ResponsiveSize


_ = Translator('reahl-web')

class Form(reahl.web.ui.Form):
    def get_js_options(self):
        return '''
        {
            errorElement: 'span',
            errorClass: 'has-danger',
            validClass: 'has-success',
            onclick: function(element, event) {
			// click on selects, radiobuttons and checkboxes
			if ( element.name in this.submitted ) {
				this.element(element);
			}
			// or option elements, check parent select in that case
			else if (element.parentNode.name in this.submitted) {
				this.element(element.parentNode);
			}
            },
            highlight: function(element) {
                $(element).closest('.form-group').removeClass('has-success').addClass('has-danger');
            },
            unhighlight: function(element) {
                $(element).closest('.form-group').removeClass('has-danger').addClass('has-success');
            },
            errorPlacement: function (error, element) {
                error.addClass('text-help')
                element.closest('.form-group').append(error);
            }
         }
    '''


class NestedForm(reahl.web.ui.NestedForm):
    def create_out_of_bound_form(self, view, unique_name):
        return Form(view, unique_name, rendered_form=self)


class TextInput(reahl.web.ui.TextInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, fuzzy=False, placeholder=False):
        super(TextInput, self).__init__(form, bound_field, fuzzy=fuzzy, placeholder=placeholder)
        self.append_class('form-control')


class PasswordInput(reahl.web.ui.PasswordInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field):
        super(PasswordInput, self).__init__(form, bound_field)
        self.append_class('form-control')


class TextArea(reahl.web.ui.TextArea):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, rows=None, columns=None):
        super(TextArea, self).__init__(form, bound_field, rows=rows, columns=rows)
        self.append_class('form-control')


class SelectInput(reahl.web.ui.SelectInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field):
        super(SelectInput, self).__init__(form, bound_field)
        self.append_class('form-control')


class CheckboxInput(reahl.web.ui.CheckboxInput):
    append_error = False
    add_default_attribute_source = False


class SingleRadioButton(reahl.web.ui.SingleRadioButton):
    append_error = False
    add_default_attribute_source = False

    def create_html_widget(self):
        return self.create_button_input()


class RadioButtonInput(reahl.web.ui.RadioButtonInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, bound_field, button_layout=None):
        self.button_layout = button_layout or ChoicesLayout()
        super(RadioButtonInput, self).__init__(form, bound_field)

    def create_main_element(self):
        main_element = super(RadioButtonInput, self).create_main_element().use_layout(self.button_layout)
        main_element.append_class('form-control-label')
        return main_element

    def add_button_for_choice_to(self, widget, choice):
        button = SingleRadioButton(self, choice)
        widget.layout.add_choice(button)


class ButtonInput(reahl.web.ui.ButtonInput):
    append_error = False
    add_default_attribute_source = False
    def __init__(self, form, event):
        super(ButtonInput, self).__init__(form, event)
        self.append_class('btn')

Button = ButtonInput


class _UnstyledHTMLFileInput(reahl.web.ui.SimpleFileInput):
    append_error = False
    add_default_attribute_source = False

    def __init__(self, form, bound_field):
        super(_UnstyledHTMLFileInput, self).__init__(form, bound_field)
        self.append_class('form-control-file')


class FileInputButton(reahl.web.ui.WrappedInput):
    def __init__(self, form, bound_field):
        label = Label(form.view)
        self.simple_input = label.add_child(_UnstyledHTMLFileInput(form, bound_field))
        self.simple_input.html_representation.append_class('btn-secondary')
        label.add_child(Span(form.view, text=_('Choose file(s)')))
        super(FileInputButton, self).__init__(self.simple_input)
        self.add_child(label)

        label.append_class('reahl-bootstrapfileinputbutton')
        label.append_class('btn')
        label.append_class('btn-primary')
        self.set_html_representation(label)

    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapfileinputbutton").bootstrapfileinputbutton({});']
        return super(FileInputButton, self).get_js(context=context) + js


class FileInput(reahl.web.ui.WrappedInput):
    def __init__(self, form, bound_field):
        file_input = FileInputButton(form, bound_field)
        super(FileInput, self).__init__(file_input)

        self.input_group = self.add_child(Div(self.view))
        self.input_group.append_class('input-group')
        self.input_group.append_class('reahl-bootstrapfileinput')
        self.set_html_representation(self.input_group)

        span = self.input_group.add_child(Span(form.view))
        span.append_class('input-group-btn')
        span.add_child(file_input)

        filename_input = self.input_group.add_child(Span(self.view, text=_('No files chosen')))
        filename_input.append_class('form-control')


    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapfileinput").bootstrapfileinput({nfilesMessage: "%s", nofilesMessage: "%s"});' % \
              (_('files chosen'), _('No files chosen'))]
        return super(FileInput, self).get_js(context=context) + js



class StaticData(reahl.web.ui.Input):
    def __init__(self, form, bound_field):
        super(StaticData, self).__init__(form, bound_field)
        p = self.add_child(P(self.view, text=self.value))
        p.append_class('form-control-static')

    def can_write(self):
        return False


class CueInput(reahl.web.ui.WrappedInput):
    def __init__(self, html_input, cue_widget):
        super(CueInput, self).__init__(html_input)
        div = self.add_child(Div(self.view))
        self.set_html_representation(div)

        div.append_class('reahl-bootstrapcueinput')
        cue_widget.append_class('reahl-bootstrapcue')

        div.add_child(html_input)
        div.add_child(cue_widget)

    def get_js(self, context=None):
        js = ['$(".reahl-bootstrapcueinput").bootstrapcueinput();']
        return super(CueInput, self).get_js(context=context) + js


class ButtonLayout(reahl.web.ui.Layout):
    def __init__(self, style=None, size=None, active=False, wide=False):
        super(ButtonLayout, self).__init__()
        assert style in ['default', 'primary', 'success', 'info', 'warning', 'danger', 'link', None]
        assert size in ['lg', 'sm', 'xs', None]
        self.style = style
        self.size = size
        self.active = active
        self.wide = wide
        
    def customise_widget(self):
        self.widget.append_class('btn')

        if isinstance(self.widget, A) and self.widget.disabled:
            self.widget.append_class('disabled')
        if self.style:
            self.widget.append_class('btn-%s' % self.style)
        if self.size:
            self.widget.append_class('btn-%s' % self.size)
        if self.active:
            self.widget.append_class('active')
        if self.wide:
            self.widget.append_class('btn-block')


class ChoicesLayout(reahl.web.ui.Layout):
    def __init__(self, inline=False):
        super(ChoicesLayout, self).__init__()
        self.inline = inline

    def add_choice(self, html_input):
        assert isinstance(html_input, (CheckboxInput, SingleRadioButton))
 
        label_widget = Label(self.view)

        if self.inline:
            label_widget.append_class('%s-inline' % html_input.input_type)
            wrapper = label_widget
        else:
            outer_div = Div(self.view)
            outer_div.append_class(html_input.input_type)
            outer_div.add_child(label_widget)
            wrapper = outer_div

        label_widget.add_child(html_input)
        label_widget.add_child(TextNode(self.view, html_input.label))

        self.widget.add_child(wrapper)

        return wrapper


class FormLayout(reahl.web.ui.Layout):
    def create_form_group(self, html_input):
        form_group = self.widget.add_child(Div(self.view))
        form_group.append_class('form-group')
        form_group.add_attribute_source(reahl.web.ui.ValidationStateAttributes(html_input, 
                                                             error_class='has-danger', 
                                                             success_class='has-success'))
        form_group.add_attribute_source(reahl.web.ui.AccessRightAttributes(html_input, disabled_class='disabled'))
        return form_group


    def add_input_to(self, parent_element, html_input):
        if not self.should_add_label(html_input):
            parent_element.use_layout(ChoicesLayout(inline=False))
            return parent_element.layout.add_choice(html_input)
        else:
            return parent_element.add_child(html_input)

    def add_validation_error_to(self, form_group, html_input):
        error_text = form_group.add_child(Span(self.view, text=html_input.validation_error.message))
        error_text.append_class('text-help')
        error_text.append_class('has-danger')
        error_text.set_attribute('for', html_input.name)
        error_text.set_attribute('generated', 'true')
        return error_text

    def add_help_text_to(self, parent_element, help_text):
        help_text_p = parent_element.add_child(P(self.view, text=help_text))
        help_text_p.append_class('text-muted')
        return help_text_p

    def add_label_to(self, form_group, html_input, hidden):
        label = form_group.add_child(Label(self.view, text=html_input.label, for_input=html_input))
        if hidden:
            label.append_class('sr-only')
        return label

    def should_add_label(self, html_input):
        return not isinstance(html_input, CheckboxInput)
        
    def add_input(self, html_input, hide_label=False, help_text=None):
        form_group = self.create_form_group(html_input)

        if self.should_add_label(html_input):
            self.add_label_to(form_group, html_input, hide_label)

        self.add_input_to(form_group, html_input)

        if html_input.get_input_status() == 'invalidly_entered':
            self.add_validation_error_to(form_group, html_input)

        if help_text:
            self.add_help_text_to(form_group, help_text)

        return html_input


class GridFormLayout(FormLayout):
    def __init__(self, label_column_size, input_column_size):
        super(GridFormLayout, self).__init__()
        self.label_column_size = label_column_size
        self.input_column_size = input_column_size

    def create_form_group(self, html_input):
        form_group = super(GridFormLayout, self).create_form_group(html_input)
        form_group.use_layout(ColumnLayout(('label', self.label_column_size), ('input', self.input_column_size)))
        return form_group

    def add_label_to(self, form_group, html_input, hidden):
        column = form_group.layout.columns['label']
        label = super(GridFormLayout, self).add_label_to(column, html_input, hidden)
        label.append_class('form-control-label')
        return label

    def add_input_to(self, parent_element, html_input):
        input_column = parent_element.layout.columns['input']
        return super(GridFormLayout, self).add_input_to(input_column, html_input)

    def add_help_text_to(self, parent_element, help_text):
        input_column = parent_element.layout.columns['input']
        return super(GridFormLayout, self).add_help_text_to(input_column, help_text)


class InlineFormLayout(FormLayout):
    def customise_widget(self):
        super(InlineFormLayout, self).customise_widget()
        self.widget.append_class('form-inline')


class Table(reahl.web.ui.Table):
    def __init__(self, view, caption_text=None, summary=None, css_id=None):
        super(Table, self).__init__(view, caption_text=caption_text, summary=summary, css_id=css_id)
        self.append_class('table')


class TableLayout(reahl.web.ui.Layout):
    def __init__(self,
                  inverse=False, border=False, compact=False,
                  striped=False, highlight_hovered=False, transposed=False, responsive=False,
                  heading_theme=None):
        assert heading_theme in [None, 'inverse', 'default'], 'Not a valid heading theme: %s' % heading_theme
        super(TableLayout, self).__init__()
        self.table_properties = {'inverse': inverse,
                                 'striped': striped,
                                 'bordered': border,
                                 'hover': highlight_hovered,
                                 'sm': compact,
                                 'reflow': transposed,
                                 'responsive': responsive}
        self.heading_theme = heading_theme

    def customise_widget(self):
        super(TableLayout, self).customise_widget()

        for table_property, is_selected in self.table_properties.items():
            if is_selected:
                self.widget.append_class('table-%s' % table_property)
        self.style_heading()

    def style_heading(self):
        if self.heading_theme:
            if not self.widget.thead:
                raise ProgrammerError('No Thead found on %s, but you asked to style is using heading_theme' % self.widget)
            self.widget.thead.append_class('thead-%s' % self.heading_theme)


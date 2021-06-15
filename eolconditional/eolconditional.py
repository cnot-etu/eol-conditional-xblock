## -*- coding: utf-8 -*-
import json
import re
import pkg_resources

from django.template import Context, Template

from webob import Response

from xblock.core import XBlock
from xblock.fields import Integer, String, Boolean, Scope
from xblock.fragment import Fragment
from xblock.exceptions import JsonHandlerError

# Make '_' a no-op so we can scrape strings
_ = lambda text: text

import logging
log = logging.getLogger(__name__)


@XBlock.needs("i18n")
class EolConditionalXBlock(XBlock):

    display_name = String(
        display_name=_("Display Name"),
        help=_("Module's display name"),
        default="Eol Conditional XBlock",
        scope=Scope.settings,
    )

    icon_class = String(
        default="other",
        scope=Scope.settings,
    )

    trigger_component = String(
        display_name = _("ID trigger component"),
        help = _("Specifies the ID of the trigger component. Remember that the identifier consists of 32 alphanumeric characters, for example: 4950f7e5541645aa920227e6dc0ea322"),
        default = "None",
        scope = Scope.settings,
    )

    conditional_component = String(
        display_name = _("ID conditional component"),
        help = _("Specifies the identifiers of the conditional components, separated by commas or newlines. Remember that the identifier is 32 alphanumeric characters long, for example: 4950f7e5541645aa920227e6dc0ea322"),
        default = "None",
        scope = Scope.settings,
    )

    has_author_view = True

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        log.error(data)
        #return data
        return data.decode("utf8")

    def student_view(self, context=None):
        context_html = self.get_context()
        template = self.render_template('static/html/eolconditional.html', context_html)
        frag = Fragment(template)
        frag.add_css(self.resource_string("static/css/eolconditional.css"))
        frag.add_javascript(self.resource_string("static/js/src/eolconditional.js"))
        settings = {
            'trigger_component'         : self.trigger_component,
            'conditional_component_list': self.get_conditional_component_list(),
            'location'                  : self.location
        }
        frag.initialize_js('EolConditionalXBlock', json_args=settings)
        return frag

    def studio_view(self, context=None):
        context_html = self.get_context()
        #template = self.render_template('static/html/studio.html', context_html)
        #frag = Fragment(template)
        frag = Fragment()
        frag.add_content(self.render_template('static/html/studio.html', context_html))
        frag.add_css(self.resource_string("static/css/eolconditional.css"))
        frag.add_javascript(self.resource_string("static/js/src/studio.js"))
        frag.initialize_js('EolConditionalStudioXBlock')
        return frag

    def author_view(self, context=None):
        context_html = self.get_context()
        template = self.render_template('static/html/author_view.html', context_html)
        frag = Fragment(template)
        frag.add_css(self.resource_string("static/css/eolconditional.css"))
        return frag

    @XBlock.handler
    def studio_submit(self, request, suffix=''):
        self.trigger_component = request.params['trigger_component']
        self.conditional_component = request.params['conditional_component']
        return Response(json.dumps({'result': 'success'}), content_type='application/json')

    def get_context(self):
        return {
            'field_trigger_component': self.fields['trigger_component'],
            'field_conditional_component': self.fields['conditional_component'],
            'conditional_component_list': self.get_conditional_component_list(),
            'xblock': self
        }

    def render_template(self, template_path, context):
        template_str = self.resource_string(template_path)
        template = Template(template_str)
        return template.render(Context(context))

    def get_conditional_component_list(self):
        conditional_component_list = re.split('\s*,*|\s*,\s*', self.conditional_component)
        return filter(None, conditional_component_list) # filter empty elements

    @XBlock.json_handler
    def publish_completion(self, data, dispatch):  # pylint: disable=unused-argument
        """
        Entry point for completion for student_view.
        Parameters:
            data: JSON dict:
                key: "completion"
                value: float in range [0.0, 1.0]
            dispatch: Ignored.
        Return value: JSON response (200 on success, 400 for malformed data)
        """
        completion_service = self.runtime.service(self, 'completion')
        if completion_service is None:
            raise JsonHandlerError(500, u"No completion service found")
        elif not completion_service.completion_tracking_enabled():
            raise JsonHandlerError(404, u"Completion tracking is not enabled and API calls are unexpected")
        if not isinstance(data['completion'], (int, float)):
            message = u"Invalid completion value {}. Must be a float in range [0.0, 1.0]"
            raise JsonHandlerError(400, message.format(data['completion']))
        elif not 0.0 <= data['completion'] <= 1.0:
            message = u"Invalid completion value {}. Must be in range [0.0, 1.0]"
            raise JsonHandlerError(400, message.format(data['completion']))
        self.runtime.publish(self, "completion", data)
        return {"result": "ok"}



    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("EolConditionalXBlock",
             """<eolconditional/>
             """),
        ]

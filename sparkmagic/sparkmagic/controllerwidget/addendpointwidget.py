# Copyright (c) 2015  aggftw@gmail.com
# Distributed under the terms of the Modified BSD License.
from sparkmagic.controllerwidget.abstractmenuwidget import AbstractMenuWidget
from sparkmagic.livyclientlib.endpoint import Endpoint
import sparkmagic.utils.constants as constants


class AddEndpointWidget(AbstractMenuWidget):

    def __init__(self, spark_controller, ipywidget_factory, ipython_display, endpoints, endpoints_dropdown_widget,
                 refresh_method):
        # This is nested
        super(AddEndpointWidget, self).__init__(spark_controller, ipywidget_factory, ipython_display, True)

        widget_width = "800px"

        self.endpoints = endpoints
        self.endpoints_dropdown_widget = endpoints_dropdown_widget
        self.refresh_method = refresh_method

        self.address_widget = self.ipywidget_factory.get_text(
            description='Address:',
            value='https://lva1-pokemon-livy01.grid.linkedin.com:8998',
            width=widget_width
        )
        self.user_widget = self.ipywidget_factory.get_text(
            description='Username:',
            value='username',
            width=widget_width
        )
        self.password_widget = self.ipywidget_factory.get_password(
            description='Password:',
            value='password',
            width=widget_width
        )
        self.auth_type = self.ipywidget_factory.get_dropdown(
            options={constants.AUTH_LDAP: constants.AUTH_LDAP,
                     constants.AUTH_KERBEROS: constants.AUTH_KERBEROS,
                     constants.AUTH_SSL: constants.AUTH_SSL,
                     constants.NO_AUTH: constants.NO_AUTH},
            description=u"Auth type:"
        )

        # Submit widget
        self.submit_widget = self.ipywidget_factory.get_submit_button(
            description='Add endpoint'
        )

        self.children = [self.ipywidget_factory.get_html(value="<br/>", width=widget_width),
                         self.address_widget, self.auth_type, self.user_widget, self.password_widget,
                         self.ipywidget_factory.get_html(value="<br/>", width=widget_width), self.submit_widget]

        for child in self.children:
            child.parent_widget = self

    def run(self):
        endpoint = Endpoint(self.address_widget.value, self.auth_type.value, self.user_widget.value, self.password_widget.value)
        self.endpoints[self.address_widget.value] = endpoint
        self.ipython_display.writeln("Added endpoint {}".format(self.address_widget.value))

        # We need to call the refresh method because drop down in Tab 2 for endpoints wouldn't refresh with the new
        # value otherwise.
        self.refresh_method()

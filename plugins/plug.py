from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint, render_template_string
from flask_appbuilder import BaseView, expose


class HideRunButtonView(BaseView):
    @expose("/")
    def list(self):
        # This custom template extends the default DAGs template and adds custom CSS.
        # The {% extends "airflow/dags.html" %} statement pulls in the built-in template.
        custom_template = """
{% extends "airflow/dags.html" %}
{% block extra_css %}
    {{ super() }}
    <style>
        /* Adjust the selector as needed.
           For example, if the run button has the class "btn-trigger-run", this rule will hide it. */
        .btn-trigger-run {
            display: none !important;
        }
    </style>
{% endblock %}
"""
        return render_template_string(custom_template)


bp = Blueprint("hide_run", __name__, template_folder="templates")


class HideRunButtonPlugin(AirflowPlugin):
    name = "hide_run_button_plugin"
    flask_blueprints = [bp]
    appbuilder_views = [
        {"name": "Hide Run Button", "category": "Admin", "view": HideRunButtonView()}
    ]

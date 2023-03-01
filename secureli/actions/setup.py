import jinja2

from secureli.services.language_support import supported_languages


class SetupAction:
    """Arranges various properties needed to set up the application itself."""

    repo_url = "https://bitbucket.org/slalom-consulting/secureli"
    confluence_url = "https://slalom.atlassian.net/wiki/spaces/STFT"

    def __init__(self, epilog_template_data: str):
        self.epilog_template_data = epilog_template_data

    def create_epilog(self):
        """Renders the epilog to display as part of the application help text."""
        template = jinja2.Template(source=self.epilog_template_data)
        return template.render(
            supported_languages=supported_languages,
            confluence_url=self.confluence_url,
            repo_url=self.repo_url,
        )

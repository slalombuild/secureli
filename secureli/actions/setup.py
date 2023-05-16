import jinja2

from secureli.services.language_support import supported_languages


class SetupAction:
    """Arranges various properties needed to set up the application itself."""

    repo_url = "https://github.com/slalombuild/secureli/blob/main/CONTRIBUTING.md"
    docs_url = "https://github.com/slalombuild/secureli/wiki"

    def __init__(self, epilog_template_data: str):
        self.epilog_template_data = epilog_template_data

    def create_epilog(self):
        """Renders the epilog to display as part of the application help text."""
        template = jinja2.Template(source=self.epilog_template_data)
        return template.render(
            supported_languages=supported_languages,
            confluence_url=self.docs_url,
            repo_url=self.repo_url,
        )

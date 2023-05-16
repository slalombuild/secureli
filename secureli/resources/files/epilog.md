{# Note: some strange whitespace in this file to get the line breaks I wanted in the terminal. #}

To install, navigate to a git repository and run [bold cyan]secureli init[/].



SeCureLI currently supports the following languages:

{% for language in supported_languages %}
    - [bold magenta]{{ language }}[/]
{% endfor %}


For more information, check us out on the GitHub wiki at {{ confluence_url }}

Interested in contributing? Check out {{ repo_url }}

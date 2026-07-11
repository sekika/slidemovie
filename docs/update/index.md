---
layout: page
title: Release
lang: en
---

To check your installed version, run: `python -m pip show slidemovie`. To upgrade to the latest version, run: `python -m pip install -U slidemovie`.

{% include release.md %}

## Specification

Here is a list of specification documents detailing the changes made in each version. These specifications were used when making code changes with Claude Code, so minor fixes made without using Claude Code are not included. Please note that the specifications are written in Japanese.

{% assign specs = site.pages | where_exp: "p", "p.path contains 'update/update-'" | sort: "version" | reverse %}

{% if specs.size == 0 %}
No specification file
{% else %}
<ul class="update-list">
{% for spec in specs %}
  <li>
    <a href="{{ spec.url | relative_url }}">{{ spec.title | default: spec.name }}</a>
  </li>
{% endfor %}
</ul>
{% endif %}

## See also
- [Release at PyPI](https://pypi.org/project/slidemovie/#history)
- [GitHub commits](https://github.com/sekika/slidemovie/commits)

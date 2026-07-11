---
layout: page
title: 履歴
lang: ja
permalink: /ja/release/
---

インストールされているバージョンを確認するには、`python -m pip show slidemovie` を実行してください。最新バージョンに更新するには、`python -m pip install -U slidemovie` を実行してください。

{% include release.md %}

## 仕様

以下は、各バージョンで実施した変更内容をまとめた仕様書の一覧です。これらの仕様書は、Claude Code を用いてコードを変更した際に作成されたものです。そのため、Claude Code を使用せずに行った軽微な修正については記載されていません。

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

## 参考
- [PyPI のリリース](https://pypi.org/project/slidemovie/#history)
- [GitHub のコミット](https://github.com/sekika/slidemovie/commits)

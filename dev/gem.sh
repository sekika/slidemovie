#!/bin/sh
cd ../slidemovie
listfiles cli.py core.py > ~/Downloads/slidemovie-code.txt
cd ../docs
listfiles *.md > ~/Downloads/slidemovie-docs.txt
cd ja
listfiles *.md > ~/Downloads/slidemovie-docs-ja.txt

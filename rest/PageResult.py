#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from flask import jsonify
import json

class PageResult:
    def __init__(self, current:int=1, size:int=10, total:int=0, pages:int=0, records:[] = None):
        self.current = current
        self.size = size
        self.total = total
        self.pages = pages
        self.records = records

    def to_json(self):
        return jsonify(self.__dict__)
    
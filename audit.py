#!/usr/bin/env python3

from random import random
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from fastapi import FastAPI, Body


class State(Enum):
    INITIALIZATION = 1
    AUDITING = 2
    CALCULATED_ITEM_RESULTS = 3
    CALCULATED_AUDIT_RESULTS = 4
    CALCULATED_AUDITOR_RESULTS = 5
    WAITING_FOR_CONTRACT = 6
    COMPLETE = 7


class Auditor(BaseModel):
    jid: str
    addr: str


class Inspection(BaseModel):
    auditor: int
    item: int
    inspection_id: int
    completed: bool = False
    finding: bool = False
    aligned: bool = False


class Audit(BaseModel):
    class Config:
        underscore_attrs_are_private = True

    name: str
    calling_contract: str
    admin_jid: str

    _bot_jid: str = ""

    _auditors: List[Auditor] = []

    _number_of_audits: int = 0
    _number_of_items: int = 0
    _number_of_audits_per_item: int = 0

    _slashing_ratio: float = 1.5

    _state: State = State.INITIALIZATION

    _inspections: List[Inspection] = []

    _item_results: List[bool] = []
    _auditor_audits_aligned: List[int] = []
    _auditor_audits_count: List[int] = []

    _auditor_compensation: List[float] = []

    def register_auditor(self, auditor: Auditor):
        self._auditors.append(auditor)

    def assign_auditors_to_items(self):
        assert self._state == State.INITIALIZATION, "Auditors already assigned"
        self._state = State.AUDITING
        auditor_iterator = 0
        for item_iterator in range(self._number_of_items):
            for _ in range(self._number_of_audits_per_item):
                self._inspections.append(
                    Inspection(
                        **{
                            "auditor": auditor_iterator,
                            "item": item_iterator,
                            "inspection_id": self.number_of_audits,
                        }
                    )
                )
                self.number_of_audits += 1
                auditor_iterator += 1
                if auditor_iterator >= len(self._auditors):
                    auditor_iterator = 0

    def get_item_audits(self, item):
        item_audits = []

        for inspect in self._inspections:
            if inspect.item == item:
                item_audits.append(inspect)

        return item_audits

    def get_auditor_audits(self, auditor):
        auditor_audits = []

        for inspect in self._inspections:
            if inspect.auditor == auditor:
                auditor_audits.append(inspect)

        return auditor_audits

    def get_outstanding_item_audits(self, item):
        outstanding_audits = []
        audits = self.get_item_audits(item)
        for audit in audits:
            if not audit.completed:
                outstanding_audits.append(audit)
        return outstanding_audits

    def get_outstanding_auditor_audits(self, auditor):
        outstanding_audits = []
        audits = self.get_auditor_audits(auditor)
        for audit in audits:
            if not audit.completed:
                outstanding_audits.append(audit)
        return outstanding_audits

    def get_outstanding_audits(self):
        outstanding_audits = []
        for audit in self._inspections:
            if not audit.completed:
                outstanding_audits.append(audit)
        return outstanding_audits

    def set_audit(self, auditor, item, finding):
        assert self._state == State.AUDITING, "Not currently auditing"
        audit_found = False
        audits = self.get_auditor_audits(auditor)
        for audit in audits:
            if audit.item == item:
                audit_found = True
                temp_audit = audit
                temp_audit.finding = finding
                temp_audit.completed = True
                self._inspections[temp_audit.inspection_id] = temp_audit
                break

        if audit_found:
            return True
        else:
            return False

    def set_audit_by_audit(self, audit, finding):
        assert self._state == State.AUDITING, "Not currently auditing"
        temp_audit = self._inspections[audit]
        temp_audit.completed = True
        temp_audit.finding = finding
        self._inspections[audit] = temp_audit

    def check_if_audit_complete(self):
        return len(self.get_outstanding_audits()) == 0

    def calculate_item_results(self):
        assert self.check_if_audit_complete(), "Audit not complete"
        assert self._state == State.AUDITING, "Not in currently auditing"
        self._state = State.CALCULATED_ITEM_RESULTS
        self._item_results = []
        for item in range(self._number_of_items):
            item_finding = 0
            for audit in self.get_item_audits(item):
                if audit.finding:
                    item_finding += 1
                else:
                    item_finding -= 1
            self._item_results.append(item_finding > 0)

    def calculate_audit_results(self):
        assert (
            self._state == State.CALCULATED_ITEM_RESULTS
        ), "Not currently calculating item results"
        self._state = State.CALCULATED_AUDIT_RESULTS
        for audit in self._inspections:
            audit.aligned = audit.finding == self._item_results[audit.item]

    def calculate_auditor_results(self):
        assert (
            self._state == State.CALCULATED_AUDIT_RESULTS
        ), "Not currently calculating audit results"
        self._state = State.CALCULATED_AUDITOR_RESULTS
        for auditor in range(len(self._auditors)):
            audit_count = 0
            aligned_count = 0
            for audit in self.get_auditor_audits(auditor):
                audit_count += 1
                if audit.aligned:
                    aligned_count += 1
            self._auditor_audits_count.append(audit_count)
            self._auditor_audits_aligned.append(aligned_count)

    def calculate_auditor_compensation(self):
        assert (
            self._state == State.CALCULATED_AUDITOR_RESULTS
        ), "Not currently calculating auditor results"
        self._state = State.WAITING_FOR_CONTRACT
        for auditor in range(len(self._auditors)):
            incorrect_answers = (
                self._auditor_audits_count[auditor]
                - self._auditor_audits_aligned[auditor]
            )
            compensation = max(
                0,
                self._auditor_audits_aligned[auditor]
                - self._slashing_ratio * incorrect_answers,
            )
            self._auditor_compensation.append(compensation)
            print(f"Auditor: {auditor}  : Compensation: {compensation}")


def test_setup():

    test_config = {
        "name": "Proto Item Checker",
        "calling_contract": "0x00alkj4t8sdfjlk3rjlfaslkfjefa;j",
        "admin_jid": "bob@foxhole",
    }
    audit = Audit(**test_config)
    audit.assign_auditors_to_items()
    mock_responses(audit)
    audit.calculate_item_results()
    audit.calculate_audit_results()
    audit.calculate_auditor_results()
    audit.calculate_auditor_compensation()
    return audit


def mock_responses(audit):
    for i in range(len(audit._inspections)):
        audit.set_audit_by_audit(i, (random() > 0.5))


def initiate_audit():
    pass

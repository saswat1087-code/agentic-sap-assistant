import pytest
from src.parsers import parser

def test_extract_root_cause():
    text = "Root Cause: Storage bin not configured\nAction Taken: Fixed config"
    assert parser.extract_root_cause(text) == "Storage bin not configured"

def test_extract_transaction_codes():
    text = "Use transaction MIGO and then COR2 to resolve"
    codes = parser.extract_transaction_codes(text)
    assert "MIGO" in codes
    assert "COR2" in codes

def test_extract_module():
    assert parser.extract_module("MIGO error in goods receipt") == "MM"
    assert parser.extract_module("QA32 inspection lot issue") == "QM"
    assert parser.extract_module("Process Order confirmation failed") == "MFG"

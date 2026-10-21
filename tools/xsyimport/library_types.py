# -*- coding: utf-8 -*-
"""Library layouts for types a Control Expert export does not define (the Modicon device DDTs).

Only an entry with confidence "confirmed" and a full member list is used. Anything else
stays skipped in the report. Fill an entry from the Control Expert project (Device DDT
type list, or an XDD export), never from memory or web snippets.

entry = {"confidence": "confirmed", "source": "...", "members": [(name, typeName, comment), ...]}
"""

LIBRARY_TYPES = {
    "T_U_DIS_STD_IN_16": {"confidence": "not found", "source": "web search, no layout found"},
    "T_U_DIS_STD_OUT_16": {"confidence": "partial", "source": "search snippet only; members incomplete"},
    "T_U_ANA_STD_IN_8": {"confidence": "not found", "source": "web search, no layout found"},
}

"""Selected TREE2100 whipsaw action220/item109/cost8 after Linda recruitment.

Explicit raw state words only; no general shop, scene-opening or journal model.
"""
from dataclasses import dataclass,replace
try:
    from .yukonseattle import State,change_money_slot_zero
except ImportError:
    from yukonseattle import State,change_money_slot_zero


class PurchaseError(ValueError):
    pass


@dataclass(frozen=True)
class WhipsawWords:
    cash_word:int
    bank_word:int
    whipsaw_word:int
    partner_word:int
    word318:int
    gate334_word:int
    def __post_init__(self):
        if any(not isinstance(v,int) or not 0<=v<=65535 for v in (self.cash_word,self.bank_word,self.whipsaw_word,self.partner_word,self.word318,self.gate334_word)):
            raise PurchaseError('Explicit unsigned16bit state words required')


@dataclass(frozen=True)
class WhipsawResult:
    state:WhipsawWords
    action_success:bool
    refusal_tree_id:int|None


def whipsaw_option_visible(whipsaw_word):
    if not isinstance(whipsaw_word,int) or not 0<=whipsaw_word<=65535:
        raise PurchaseError('Explicit unsigned16bit whipsaw word required')
    return whipsaw_word==0


def purchase_selected_whipsaw(state,action=(220,109,8,0),conv_first_word=17):
    if action!=(220,109,8,0) or conv_first_word!=17 or state.partner_word!=4 or state.whipsaw_word!=0:
        raise PurchaseError('Only selected unowned Seattle whipsaw with Linda context recovered')
    total=(state.cash_word+state.bank_word)&65535
    signed_total=total-65536 if total>=32768 else total
    if signed_total<8:
        return WhipsawResult(state,False,600)
    # This adapter uses only cash/bank/gate arithmetic. Its unused flag344
    # placeholder is not a recovered game default and is never returned.
    money,_=change_money_slot_zero(State(state.cash_word,state.bank_word,4,state.gate334_word,0),-8)
    next_state=replace(state,cash_word=money.cash_word,bank_word=money.bank_word)
    if not state.gate334_word:
        next_state=replace(next_state,whipsaw_word=1,word318=17)
    return WhipsawResult(next_state,True,None)

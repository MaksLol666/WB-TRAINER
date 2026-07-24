from aiogram.fsm.state import State, StatesGroup


class RegisterState(StatesGroup):
    waiting_invite_code = State()


class CreatePVZState(StatesGroup):
    waiting_name = State()


class AddQuestionState(StatesGroup):
    waiting_category = State()
    waiting_type = State()
    waiting_question = State()
    waiting_answers = State()
    waiting_correct = State()
    waiting_explanation = State()


class TestState(StatesGroup):
    answering = State()


class DeleteState(StatesGroup):
    waiting_employee_id = State()
    waiting_pvz_id = State()
    confirm_delete = State()


class AssignOwnerState(StatesGroup):
    waiting_user_id = State()
    waiting_pvz_id = State()


class RemoveOwnerState(StatesGroup):
    waiting_owner_id = State()

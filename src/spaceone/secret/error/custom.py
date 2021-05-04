# -*- coding: utf-8 -*-

from spaceone.core.error import *

class ERROR_DEFINE_SECRET_BACKEND(ERROR_BASE):
    _message = 'Secret Backend is not defined. {backend})'

class ERROR_ALREADY_EXIST_SECRET_IN_GROUP(ERROR_BASE):
    _message = 'Secret is already exist in group.(secret_group_id = {secret_group_id}, secret_id = {secret_id})'


class ERROR_NOT_EXIST_SECRET_IN_GROUP(ERROR_BASE):
    _message = 'Secret is not exist in group.(secret_group_id = {secret_group_id}, secret_id = {secret_id})'


class ERROR_WRONG_ENCRYPT_ALGORITHM(ERROR_HANDLER_CONFIGURATION):
    _message = 'EncryptAlgorithm({encrypt_algorithm}) is not supported.'
    

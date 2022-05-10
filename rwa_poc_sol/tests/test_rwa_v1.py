import time
import pytest
from brownie import VRFConsumer, convert, network, config, exceptions
from scripts.helpful_scripts import (
    get_account,
    get_contract,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    listen_for_event,
)
from scripts.deploy import deploy_contract, deploy_with_users, do_reports
import pytest


def test_application_with_bond_of_correct_size():
    # Arrange
    contract = deploy_contract()
    # Act
    tx = contract.applyAsChecker(
        {"from": get_account(1), "value": config["bond_price"]}
    )
    # Assert
    assert contract.balance() == config["bond_price"]
    assert tx.events["CheckerApplied"]["checker"] == get_account(1)


def test_application_with_bond_too_small():
    # Arrange
    contract = deploy_contract()
    # Act
    # Assert
    with pytest.raises(exceptions.VirtualMachineError):
        tx = contract.applyAsChecker(
            {"from": get_account(1), "value": config["bond_price"] - 1}
        )


def test_application_with_bond_too_large():
    # Arrange
    contract = deploy_contract()
    # Act
    # Assert
    with pytest.raises(exceptions.VirtualMachineError):
        tx = contract.applyAsChecker(
            {"from": get_account(1), "value": config["bond_price"] + 1}
        )


def test_application_twice_from_same_account():
    contract = deploy_contract()

    tx = contract.applyAsChecker(
        {"from": get_account(1), "value": config["bond_price"]}
    )

    with pytest.raises(exceptions.VirtualMachineError):
        tx = contract.applyAsChecker(
            {"from": get_account(1), "value": config["bond_price"]}
        )


def test_funding():
    # Arrange
    contract = deploy_contract()
    # Act
    tx = contract.fund({"from": get_account(0), "value": 1.1 * 10**18})
    # Assert
    assert contract.balance() == 1.1 * 10**18


def test_report():
    # Arrange
    contract = deploy_with_users()
    contract.startProject()
    do_reports(contract, True)
    # Assert
    # Need to figure out some assert here


def test_stopping_project_with_incomplete_repots():
    # Arrange
    contract = deploy_with_users()
    contract.startProject()
    # Act
    # Assert
    with pytest.raises(exceptions.VirtualMachineError):
        tx = contract.stopProject()
    assert contract.status() == 1


def test_stopping_project_with_repots_done():
    # Arrange
    contract = deploy_with_users()
    contract.startProject()
    do_reports(contract, True)
    # Act
    tx = contract.stopProject()
    # Assert
    assert contract.status() == 2

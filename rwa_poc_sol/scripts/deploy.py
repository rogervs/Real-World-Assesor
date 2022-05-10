from brownie import rwa, config, accounts
from scripts.helpful_scripts import get_account


def deploy_contract():
    admin = get_account()
    contract = rwa.deploy(
        config["bond_price"],
        config["checks_per_item"],
        config["penalty_ratio"],
        {"from": admin},
    )
    return contract


def add_checkers(contract, number=3):
    txs = []
    for count in range(1, number + 1):
        txs.append(
            contract.applyAsChecker(
                {"from": get_account(count), "value": config["bond_price"]}
            )
        )
    return txs


def do_reports(contract, answer: bool):
    checker_counter = contract.checkerCounter()
    checker_accounts = accounts[1 : 1 + checker_counter]
    txs = []
    checker_iterator = 0
    num_items = contract.numItems()
    for item_counter in range(num_items):
        for item_check_iterator in range(config["checks_per_item"]):
            tx = contract.report(
                item_counter, answer, {"from": checker_accounts[checker_iterator]}
            )
            txs.append(tx)
            checker_iterator += 1
            if checker_iterator == 1 or checker_iterator == 2:
                answer = not answer
            if checker_iterator == checker_counter:
                checker_iterator = 0
    txs.append(tx)
    return txs


def deploy_with_users():
    contract = deploy_contract()
    add_checkers(contract)
    contract.setItems(3)
    return contract


def cycle():
    contract = deploy_with_users()
    contract.startProject()
    do_reports(contract, True)
    contract.stopProject()
    contract.itemResultsProcess()
    tx = contract.checkerResultsProcess()
    return contract, tx


def main():
    contract = deploy_contract()

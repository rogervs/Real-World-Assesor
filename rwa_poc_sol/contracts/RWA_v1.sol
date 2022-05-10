// SPDX-License-Identifier: MIT
//

pragma solidity >=0.8.7 <0.9.0;

import "@openzeppelin/contracts/access/Ownable.sol";

contract rwa is Ownable {
    uint256 public numItems;
    address Owner;

    enum projectStatus {
        NotStarted,
        Running,
        Stopped,
        Completed
    }
    projectStatus public status = projectStatus.NotStarted;

    uint public checkerCounter = 0;
    mapping(address => bool) public checkerPresent;
    address[] public checkerList;

    uint8 public checksPerItem;
    uint8 public penaltyRatio;
    uint256 public bondAmount;
    uint256 public fundAmount;

    event ItemsSet(uint256 numItems);
    event CheckerApplied(address checker, uint checkerCounter, address[] checkerList);
    event StatusChanged(projectStatus newStatus);
    event Funded(uint256 fundAmount);

    constructor(uint256 _bondAmount, uint8 _checksPerItem, uint8 _penaltyRatio) {
        require(_checksPerItem % 2 != 0);
        checksPerItem = _checksPerItem;
        penaltyRatio = _penaltyRatio;
        Owner = msg.sender;
        bondAmount = _bondAmount;
    }

    modifier requireState(projectStatus requiredStatus) {
        require(status == requiredStatus, "Cannot transition to requested state from current state");
        _;
    }

    modifier bondRequired() {
        require(msg.value == bondAmount, "Bond deposited not equal to required bond amount");
        _;
    }

    function setItems(uint256 _numItems)
        external
        onlyOwner
        requireState(projectStatus.NotStarted)
    {
        numItems = _numItems;
        emit ItemsSet(numItems);
    }

    function fund() external payable {
        fundAmount += msg.value;
        emit Funded(fundAmount);
    }

    mapping(address => uint) checkerToIdMap;

    function setWallet(address _wallet) internal {
        checkerPresent[_wallet] = true;
        checkerToIdMap[_wallet] = checkerCounter;
        checkerList.push(_wallet);
        checkerCounter += 1;
    }

    function walletPresent(address _wallet) internal returns(bool) {
        return checkerPresent[_wallet];
    }

    function applyAsChecker()
        external
        payable
        requireState(projectStatus.NotStarted)
        bondRequired
    {
        require(!walletPresent(msg.sender), "User already registered as a checker");
        setWallet(msg.sender);
        emit CheckerApplied(msg.sender, checkerCounter, checkerList);
    }

    event Counted(uint itemCounter);

    struct CheckerItemReport {
        uint checkerId;
        bool responded;
        bool answer;
    }

    mapping(uint => CheckerItemReport[]) public itemToCheckers;

    // event ItemCounterEvent(uint itemCounter);
    // event ItemCheckIteratorEvent(uint itemCheckIterator);
    // event CheckerIteratorEvent(uint checkerIterator);
    event CIAssignment(uint item, uint itemSpot, uint checkerId);

    function startProject() external requireState(projectStatus.NotStarted) onlyOwner {
        status = projectStatus.Running;
        uint itemCounter;
        uint checkerIterator;
        uint itemCheckIterator;
        CheckerItemReport memory tmp;
        // Assign items to checkers
        for (itemCounter = 0; itemCounter < numItems; itemCounter++ ) {
            for (itemCheckIterator = 0; itemCheckIterator < checksPerItem; itemCheckIterator++ ){
                tmp.checkerId = checkerIterator;
                itemToCheckers[itemCounter].push(tmp);
                emit CIAssignment(itemCounter, itemCheckIterator, checkerIterator);
                checkerIterator += 1;
                if (checkerIterator == checkerCounter) {
                    checkerIterator = 0;
                    }
            }
        }
        emit StatusChanged(status);
    }

    event itemStatusReported(CheckerItemReport item);

    function report(uint _item, bool correct) external {
        CheckerItemReport[] memory localCheckers = itemToCheckers[_item];
        uint id = 0;
        bool found = false;
        for (id = 0; id < localCheckers.length; id++){
           if (checkerList[localCheckers[id].checkerId] == msg.sender) {
               itemToCheckers[_item][id].responded = true;
               itemToCheckers[_item][id].answer = correct;
               found = true;
               emit itemStatusReported(itemToCheckers[_item][id]);
            }
        }
        require(found, "Checker not assigned to item");
    }


    event MissingReport (CheckerItemReport item);

    function stopProject() external requireState(projectStatus.Running) onlyOwner {
        uint itemIterator;
        uint checkIterator;
        bool cleared = true;
        for (itemIterator=0; itemIterator < numItems && cleared; itemIterator++ ) {
            for (checkIterator=0; checkIterator < checksPerItem  && cleared; checkIterator++) {
                cleared = itemToCheckers[itemIterator][checkIterator].responded;
                if (!cleared) {
                    emit MissingReport(itemToCheckers[itemIterator][checkIterator]);
                    require(cleared, "Report missing");
                }
            }
        }
        // Check who needs to be paid how much and pay them
        require(cleared, "Not all checks have been completed");
        status = projectStatus.Stopped;
        emit StatusChanged(status);
    }

    event ItemOutcomeEvent(bool itemOutcome);

    bool[] public itemOutcomes;

    function itemResultsProcess() external requireState(projectStatus.Stopped) {
        delete itemOutcomes;
        uint itemIterator;
        uint checkIterator;
        int trueCount;
        bool itemOutcome;
        for (itemIterator=0; itemIterator < numItems; itemIterator++ ) {
            trueCount = 0;
            for (checkIterator=0; checkIterator < checksPerItem; checkIterator++) {
                if (itemToCheckers[itemIterator][checkIterator].answer) {
                    trueCount += 1;
                }
                else {
                    trueCount -= 1;
                    }
            }
            itemOutcome = trueCount > 0;
            emit ItemOutcomeEvent(itemOutcome);
            itemOutcomes.push(itemOutcome);
        }
    }

    uint[] public checkerScore;
    uint[] public checkerNumChecks;

    event CheckerOutcomeEvent (uint checkerId, uint itemId, bool correct);


    function checkerResultsProcess() external requireState(projectStatus.Stopped) {
        uint itemIterator;
        uint checkIterator;
        bool answer;
        bool correct;
        uint checkerId ;
        uint[] memory checkerScoreTemp = new uint[](checkerCounter);
        uint[] memory checkerNumChecksTemp = new uint[](checkerCounter);



        for (itemIterator=0; itemIterator < numItems; itemIterator++ ) {
            for (checkIterator=0; checkIterator < checksPerItem; checkIterator++) {
                checkerId = itemToCheckers[itemIterator][checkIterator].checkerId;
                answer = itemToCheckers[itemIterator][checkIterator].answer;
                correct = (answer == itemOutcomes[itemIterator]);
                checkerNumChecksTemp[checkerId] = checkerNumChecksTemp[checkerId] + 1;
                if (correct) {
                    checkerScoreTemp[checkerId] = checkerScoreTemp[checkerId] + 1;
                }
                emit CheckerOutcomeEvent (checkerId, itemIterator, correct);
            }
        }
        checkerScore = checkerScoreTemp;
        checkerNumChecks = checkerNumChecksTemp;
    }

    function checkerPayout() external requireState(projectStatus.Stopped) {
        uint checkerIterator;
        for (checkerIterator=0; checkerIterator < checkerCounter; checkerIterator++) {

        }
    }


    function completeProject() external requireState(projectStatus.Stopped) onlyOwner  {
        status = projectStatus.Completed;
        emit StatusChanged(status);
        // Everything is done, project dead.
    }
}

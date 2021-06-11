package status

import (
	"errors"
	"fmt"
	"strings"

	"github.com/dropseed/commitstat/internal/parse"
)

type state string

const (
	stateSuccess state = "success"
	stateFailure state = "failure"
	stateError   state = "error"
)

type Status struct {
	State       state
	Description string
}

func NewStatus(stat, comparisonStat, comparisonRef, goal string) (*Status, error) {
	state, description, err := compareStats(stat, comparisonStat, comparisonRef, goal)
	if err != nil {
		return nil, err
	}
	return &Status{
		State:       state,
		Description: description,
	}, nil
}

func compareStats(stat, comparisonStat, comparisonRef, goal string) (state, string, error) {
	// IMPORTANT: the current stat needs to be the first thing in the description
	// because that's how we will parse it back off
	if comparisonStat == "" {
		return stateError, fmt.Sprintf("%s - nothing to compare on %s (stat is either new or being processed simultaneously)", comparisonRef, stat), nil
	}

	statNum, statUnits, err := parse.ParseStatNumber(stat)
	if err != nil {
		return stateError, "Unable to parse stat", err
	}

	prevStatNum, prevStatUnits, err := parse.ParseStatNumber(comparisonStat)
	if err != nil {
		return stateError, fmt.Sprintf("Unable to parse comparison stat from %s", comparisonRef), err
	}

	if statUnits != prevStatUnits {
		return stateError, fmt.Sprintf("Stats are not the same units: %s vs %s", statUnits, prevStatUnits), nil
	}

	if goal == "decrease" {
		if statNum < prevStatNum {
			diff := strings.TrimRight(fmt.Sprintf("%f", prevStatNum-statNum), ".0")
			return stateSuccess, fmt.Sprintf("%s - decreased by %s%s (%s on %s)", stat, diff, statUnits, comparisonStat, comparisonRef), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - same as %s", stat, comparisonRef), nil
		} else {
			diff := strings.TrimRight(fmt.Sprintf("%f", statNum-prevStatNum), ".0")
			return stateFailure, fmt.Sprintf("%s - increased by %s%s (%s on %s)", stat, diff, statUnits, comparisonStat, comparisonRef), nil
		}
	} else if goal == "increase" {
		if statNum > prevStatNum {
			diff := strings.TrimRight(fmt.Sprintf("%f", statNum-prevStatNum), ".0")
			return stateSuccess, fmt.Sprintf("%s - increased by %s%s (%s on %s)", stat, diff, statUnits, comparisonStat, comparisonRef), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - same as %s", stat, comparisonRef), nil
		} else {
			diff := strings.TrimRight(fmt.Sprintf("%f", prevStatNum-statNum), ".0")
			return stateFailure, fmt.Sprintf("%s - decreased by %s%s (%s on %s)", stat, diff, statUnits, comparisonStat, comparisonRef), nil
		}
	} else {
		return stateError, "unknown goal", errors.New("unknown goal")
	}
}

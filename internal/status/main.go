package status

import (
	"errors"
	"fmt"

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

	statNum, err := parse.ParseStatNumber(stat)
	if err != nil {
		return stateError, "unable to parse stat", err
	}

	prevStatNum, err := parse.ParseStatNumber(comparisonStat)
	if err != nil {
		return stateError, fmt.Sprintf("unable to parse comparison stat from %s", comparisonRef), err
	}

	if goal == "decrease" {
		if statNum < prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - less than %s (%s)", stat, comparisonStat, comparisonRef), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - no change compared to %s", stat, comparisonRef), nil
		} else {
			return stateFailure, fmt.Sprintf("%s - more than %s (%s)", stat, comparisonStat, comparisonRef), nil
		}
	} else if goal == "increase" {
		if statNum > prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - more than %s (%s)", stat, comparisonStat, comparisonRef), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - no change compared to %s", stat, comparisonRef), nil
		} else {
			return stateFailure, fmt.Sprintf("%s - less than %s (%s)", stat, comparisonStat, comparisonRef), nil
		}
	} else {
		return stateError, "unknown goal", errors.New("unknown goal")
	}
}

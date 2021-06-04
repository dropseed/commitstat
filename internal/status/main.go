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
	Stat           string
	ComparisonStat string
	Goal           string
	State          state
	Description    string
}

func NewStatus(stat, comparisonStat, goal string) (*Status, error) {
	state, description, err := compareStats(stat, comparisonStat, goal)
	if err != nil {
		return nil, err
	}
	return &Status{
		Stat:           stat,
		ComparisonStat: comparisonStat,
		Goal:           goal,
		State:          state,
		Description:    description,
	}, nil
}

func compareStats(stat, comparisonStat, goal string) (state, string, error) {
	// IMPORTANT: the current stat needs to be the first thing in the description
	// because that's how we will parse it back off
	if comparisonStat == "" {
		return stateSuccess, fmt.Sprintf("%s is the first value seen", stat), nil
	}

	statNum, err := parse.ParseStatNumber(stat)
	if err != nil {
		return stateError, "unable to parse stat", err
	}

	prevStatNum, err := parse.ParseStatNumber(comparisonStat)
	if err != nil {
		return stateError, "unable to parse comparison stat", err
	}

	if goal == "decrease" {
		if statNum < prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - less than %s", stat, comparisonStat), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - no change", stat), nil
		} else {
			return stateFailure, fmt.Sprintf("%s - more than %s", stat, comparisonStat), nil
		}
	} else if goal == "increase" {
		if statNum > prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - more than %s", stat, comparisonStat), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s - no change", stat), nil
		} else {
			return stateFailure, fmt.Sprintf("%s - less than %s", stat, comparisonStat), nil
		}
	} else {
		return stateError, "unknown goal", errors.New("unknown goal")
	}
}

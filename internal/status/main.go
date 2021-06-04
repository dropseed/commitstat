package status

import (
	"errors"
	"fmt"
	"regexp"
	"strconv"
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

	statNum, err := parseStatNumber(stat)
	if err != nil {
		return stateError, "unable to parse stat", err
	}

	prevStatNum, err := parseStatNumber(comparisonStat)
	if err != nil {
		return stateError, "unable to parse comparison stat", err
	}

	if goal == "decrease" {
		if statNum <= prevStatNum {
			return stateSuccess, fmt.Sprintf("%s is less than %s", stat, comparisonStat), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s is same as %s", stat, comparisonStat), nil
		} else {
			return stateFailure, fmt.Sprintf("%s is more than %s", stat, comparisonStat), nil
		}
	} else if goal == "increase" {
		if statNum >= prevStatNum {
			return stateSuccess, fmt.Sprintf("%s is more than %s", stat, comparisonStat), nil
		} else if statNum == prevStatNum {
			return stateSuccess, fmt.Sprintf("%s is same as %s", stat, comparisonStat), nil
		} else {
			return stateFailure, fmt.Sprintf("%s is less than %s", stat, comparisonStat), nil
		}
	} else {
		return stateError, "unknown goal", errors.New("unknown goal")
	}
}

func parseStatNumber(s string) (float64, error) {
	if num, err := strconv.ParseFloat(s, 32); err == nil {
		return num, nil
	} else {
		return 0.0, err
	}
}

// ParseStatFromDescription expects the stat to be the first part of the string and could have a %, mb, or something directly after it
func ParseStatFromDescription(text string) string {
	re := regexp.MustCompile("^[\\d\\.]+\\S*")
	matches := re.FindAllString(text, 1)
	if len(matches) == 1 {
		return matches[0]
	}
	return ""
}

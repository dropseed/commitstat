package parse

import (
	"errors"
	"fmt"
	"regexp"
	"strconv"
)

func ParseStatFromString(s, regex string) (string, error) {
	re := regexp.MustCompile(regex)
	matches := re.FindStringSubmatch(s)
	if len(matches) == 0 {
		return "", errors.New("regex didn't match anything")
	}
	if len(matches) != 2 {
		return "", fmt.Errorf("regex needs to include exactly 1 capture group using \"()\"\ncurrent pattern matched:\n%v", matches)
	}

	return matches[1], nil
}

func ParseStatNumber(s string) (float64, string, error) {
	re := regexp.MustCompile(`^([\d\.]+)(\S*)`)
	matches := re.FindAllStringSubmatch(s, 1)
	if num, err := strconv.ParseFloat(matches[0][1], 64); err == nil {
		return num, matches[0][2], nil
	} else {
		return 0.0, "", err
	}
}

// ParseStatFromDescription expects the stat to be the first part of the string and could have a %, mb, or something directly after it
func ParseStatFromDescription(text string) string {
	re := regexp.MustCompile(`^[\d\.]+\S*`)
	matches := re.FindAllString(text, 1)
	if len(matches) == 1 {
		return matches[0]
	}
	return ""
}

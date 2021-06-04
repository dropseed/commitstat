package parse

import (
	"errors"
	"fmt"
	"regexp"
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

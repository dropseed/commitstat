package parse

import "testing"

func TestParsePercentUnits(t *testing.T) {
	num, units, err := ParseStatNumber("34%")
	if err != nil {
		t.Error(err)
	}
	if num != 34 {
		t.Error(num)
	}
	if units != "%" {
		t.Error(units)
	}
}

func TestParseMBUnits(t *testing.T) {
	num, units, err := ParseStatNumber("41.56MB")
	if err != nil {
		t.Error(err)
	}
	if num != 41.56 {
		t.Error(num)
	}
	if units != "MB" {
		t.Error(units)
	}
}

func TestParseNoUnits(t *testing.T) {
	num, units, err := ParseStatNumber("38")
	if err != nil {
		t.Error(err)
	}
	if num != 38 {
		t.Error(num)
	}
	if units != "" {
		t.Error(units)
	}
}

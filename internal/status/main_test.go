package status

import "testing"

func TestCompareDecreaseSuccess(t *testing.T) {
	state, description, err := compareStats("34%", "35%", "master", "decrease")
	if err != nil {
		t.Error(err)
	}
	if state != stateSuccess {
		t.Error(state)
	}
	if description != "34% - decreased by 1% (35% on master)" {
		t.Error(description)
	}
}
func TestCompareDecreaseFail(t *testing.T) {
	state, description, err := compareStats("35.56%", "35%", "master", "decrease")
	if err != nil {
		t.Error(err)
	}
	if state != stateFailure {
		t.Error(state)
	}
	if description != "35.56% - increased by 0.56% (35% on master)" {
		t.Error(description)
	}
}

func TestCompareIncreaseSuccess(t *testing.T) {
	state, description, err := compareStats("34mb", "35mb", "master", "increase")
	if err != nil {
		t.Error(err)
	}
	if state != stateFailure {
		t.Error(state)
	}
	if description != "34mb - decreased by 1mb (35mb on master)" {
		t.Error(description)
	}
}
func TestCompareIncreaseFail(t *testing.T) {
	state, description, err := compareStats("35.56mb", "35mb", "master", "increase")
	if err != nil {
		t.Error(err)
	}
	if state != stateSuccess {
		t.Error(state)
	}
	if description != "35.56mb - increased by 0.56mb (35mb on master)" {
		t.Error(description)
	}
}
func TestCompareIncreaseEqual(t *testing.T) {
	state, description, err := compareStats("35mb", "35mb", "master", "increase")
	if err != nil {
		t.Error(err)
	}
	if state != stateSuccess {
		t.Error(state)
	}
	if description != "35mb - same as master" {
		t.Error(description)
	}
}

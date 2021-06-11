package github

import (
	"encoding/json"
	"io/ioutil"
	"os"
)

type githubRepository struct {
	DefaultBranch string `json:"default_branch"`
}

type githubPushEvent struct {
	Before     string            `json:"before"`
	Ref        string            `json:"ref"`
	Repository *githubRepository `json:"repository"`
}

func NewGitHubPushEvent(path string) *githubPushEvent {
	jsonFile, err := os.Open(path)
	if err != nil {
		panic(err)
	}

	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)

	var event githubPushEvent
	if err := json.Unmarshal([]byte(byteValue), &event); err != nil {
		panic(err)
	}

	return &event
}

func (event *githubPushEvent) GetComparisonRef() string {
	if event.Ref == "refs/heads/"+event.Repository.DefaultBranch {
		// This is a push to master/main, so compare stat to previous commit sha
		// (shorten for readability)
		return event.Before[:7]
	}
	// Compare to latest on the default branch
	return event.Repository.DefaultBranch
}

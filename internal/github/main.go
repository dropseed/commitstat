package github

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"

	commitstatStatus "github.com/dropseed/commitstat/internal/status"
)

type githubStatus struct {
	State       string `json:"state"`
	Description string `json:"description"`
	TargetURL   string `json:"target_url"`
	Context     string `json:"context"`
}

type githubRefStatus struct {
	Statuses []*githubStatus `json:"statuses"`
}

func FetchRefStat(repo, ref, statName, apiToken string) (string, error) {
	statusURL := fmt.Sprintf("/repos/%s/commits/%s/status", repo, ref)
	resp, body, err := request("GET", statusURL, nil, apiToken)
	if err != nil {
		return "", err
	}

	if resp.StatusCode != 200 {
		return "", fmt.Errorf("%s returned HTTP %d", statusURL, resp.StatusCode)
	}

	var refStatus githubRefStatus
	if err := json.Unmarshal([]byte(body), &refStatus); err != nil {
		return "", err
	}

	context := githubContextForStatName(statName)

	for _, status := range refStatus.Statuses {
		if status.Context == context {
			return commitstatStatus.ParseStatFromDescription(status.Description), nil
		}
	}

	return "", nil
}

func SubmitStatus(repo, sha, statName string, status *commitstatStatus.Status, apiToken string) error {
	targetURL := ""
	if runID := os.Getenv("GITHUB_RUN_ID"); runID != "" {
		targetURL = fmt.Sprintf("%s/%s/actions/runs/%s", os.Getenv("GITHUB_SERVER_URL"), os.Getenv("GITHUB_REPOSITORY"), runID)
	}
	githubStatus := &githubStatus{
		State:       string(status.State),
		Description: status.Description,
		TargetURL:   targetURL,
		Context:     githubContextForStatName(statName),
	}
	githubStatusJSON, _ := json.Marshal(githubStatus)
	statusesURL := fmt.Sprintf("/repos/%s/statuses/%s", repo, sha)
	resp, _, err := request("POST", statusesURL, githubStatusJSON, apiToken)
	if err != nil {
		return err
	}

	if resp.StatusCode != 201 {
		return fmt.Errorf("%s returned HTTP %d", statusesURL, resp.StatusCode)
	}

	return nil
}

func githubContextForStatName(statName string) string {
	return "commitstat/" + statName
}

func request(verb string, url string, input []byte, apiToken string) (*http.Response, string, error) {
	baseUrl := "https://api.github.com"
	if overrideURL := os.Getenv("GITHUB_API_URL"); overrideURL != "" {
		baseUrl = overrideURL
	}

	client := &http.Client{}

	req, err := http.NewRequest(verb, baseUrl+url, bytes.NewBuffer(input))
	if err != nil {
		return nil, "", err
	}

	req.Header.Add("Authorization", "token "+apiToken)
	req.Header.Add("User-Agent", "commitstat")
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return nil, "", err
	}

	body, err := ioutil.ReadAll(resp.Body)
	resp.Body.Close()
	return resp, string(body), err
}

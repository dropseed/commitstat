package main

import (
	"errors"
	"fmt"
	"io/ioutil"
	"os"
	"strings"

	"github.com/dropseed/commitstat/internal/github"
	"github.com/dropseed/commitstat/internal/parse"
	"github.com/dropseed/commitstat/internal/status"
	"github.com/dropseed/commitstat/internal/version"
	"github.com/spf13/cobra"
)

var verbose bool
var regex string
var statName string
var goal string

var rootCmd = &cobra.Command{
	Use:     "commitstat [file to parse]",
	Version: version.WithMeta,
	Args: func(cmd *cobra.Command, args []string) error {
		if len(args) != 1 {
			return errors.New("arg should be a path or \"-\" to read from stdin")
		}
		return nil
	},
	Run: func(cmd *cobra.Command, args []string) {
		var contents string

		if args[0] == "-" {
			bytes, _ := ioutil.ReadAll(os.Stdin)
			contents = string(bytes)
		} else {
			filename := args[0]
			fileContent, err := ioutil.ReadFile(filename)
			if err != nil {
				printErrAndExitFailure(err)
			}
			contents = string(fileContent)
		}

		// Assume stat was given directly by default
		stat := strings.TrimSpace(contents)

		if regex != "" {
			fmt.Printf("Parsing stat using: %s\n", regex)
			parsedStat, err := parse.ParseStatFromString(contents, regex)
			if err != nil {
				printErrAndExitFailure(err)
			}
			stat = parsedStat
		}

		fmt.Printf("Parsed stat value: %s\n", stat)

		if os.Getenv("GITHUB_ACTIONS") != "" {
			if event := os.Getenv("GITHUB_EVENT_NAME"); event != "push" {
				println("Stat comparisons are only made for \"push\" events")
				return
			}

			githubToken := os.Getenv("GITHUB_TOKEN")
			if githubToken == "" {
				printErrAndExitFailure(errors.New("GITHUB_TOKEN is required to submit stats"))
			}

			repo := os.Getenv("GITHUB_REPOSITORY")
			if repo == "" {
				printErrAndExitFailure(errors.New("GITHUB_REPOSITORY is required"))
			}

			pushEvent := github.NewGitHubPushEvent(os.Getenv("GITHUB_EVENT_PATH"))
			comparisonRef := pushEvent.GetComparisonRef()
			fmt.Printf("Fetching comparision stat from %s\n", comparisonRef)

			comparisonStat, err := github.FetchRefStat(repo, comparisonRef, statName, githubToken)
			if err != nil {
				printErrAndExitFailure(err)
			}

			if comparisonStat != "" {
				fmt.Printf("Comparision stat from %s: %s\n", comparisonRef, comparisonStat)
			} else {
				fmt.Printf("No comparison stat found on %s\n", comparisonRef)
			}

			status, err := status.NewStatus(stat, comparisonStat, goal)
			if err != nil {
				printErrAndExitFailure(err)
			}

			fmt.Printf("%s: %s\n", status.State, status.Description)

			sha := os.Getenv("GITHUB_SHA")
			if err := github.SubmitStatus(repo, sha, statName, status, githubToken); err != nil {
				printErrAndExitFailure(err)
			}
		} else {
			println("Run in GitHub Actions to create commit statuses")
		}
	},
}

func init() {
	rootCmd.Flags().StringVar(&regex, "regex", "", "regex to parse the stat (optional)")
	rootCmd.Flags().StringVar(&statName, "name", "", "name for the stat")
	rootCmd.MarkFlagRequired("name")
	rootCmd.Flags().StringVar(&goal, "goal", "decrease", "goal for the stat")
}

func printErrAndExitFailure(err error) {
	println(err.Error())
	os.Exit(1)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		printErrAndExitFailure(err)
	}
}

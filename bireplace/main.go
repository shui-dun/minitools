package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	inputFile := flag.String("i", "", "Input file path")
	outputFile := flag.String("o", "", "Output file path")
	oldStr := flag.String("old", "", "String to replace")
	newStr := flag.String("new", "", "New string")
	flag.Parse()

	if *inputFile == "" || *outputFile == "" || *oldStr == "" || *newStr == "" {
		flag.Usage()
		os.Exit(1)
	}

	if len(*oldStr) != len(*newStr) {
		fmt.Println("Error: Old and new strings must be the same length for binary replacement")
		os.Exit(1)
	}

	count, err := FileReplace(*inputFile, *outputFile, *oldStr, *newStr)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Replaced %d occurrences\n", count)
}
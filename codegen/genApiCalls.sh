#!/bin/bash

rootDir='..'
apiCodegenFolder=.
apiDefinitionsFolder=$apiCodegenFolder/definitions/google/dist
apiGeneratorsFolder=$apiCodegenFolder
apiLanguage=python

apiOutputFolder=src/harness/api

declare -A apiFiles=( \
  ["google"]="google-maps-platform-openapi3.yml" \
)

for package in "${!apiFiles[@]}"
do
  apiDefinitionsFile="$apiDefinitionsFolder/${apiFiles[$package]}"
  outputFolder="$apiOutputFolder/$package"
  outputName="${package}_client"
  outputPackageName="${outputFolder//\//.}.$outputName"
  outputFalsePath="$outputFolder/$apiOutputFolder"

  rm -rf "../${outputFolder:?}"

  java -jar "$apiGeneratorsFolder/openapi-generator-cli.jar" generate \
    -i "$apiDefinitionsFile" \
    -g "$apiLanguage" \
    -o "$rootDir/$outputFolder" \
    --package-name "$outputPackageName"

  mv "$rootDir/$outputFolder/$outputFolder/$outputName" "$rootDir/$outputFolder/$outputName"
  rm -rf "${rootDir:?}/${outputFalsePath:?}"
done

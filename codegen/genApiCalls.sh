#!/bin/bash

rootDir='..'
apiCodegenFolder=.
apiDefinitionsFolder=$apiCodegenFolder/definitions
apiGeneratorsFolder=$apiCodegenFolder
apiLanguage=python

apiOutputFolder=api

declare -A apiFiles=( \
#  ["google"]="google/dist/google-maps-platform-openapi3.yml" \
  ["worldpop"]="worldpop.yml" \
)

for package in "${!apiFiles[@]}"
do
  apiDefinitionsFile="$apiDefinitionsFolder/${apiFiles[$package]}"
  outputFolder="$apiOutputFolder/$package"
  outputName="${package}_client"
  outputPackageName="$outputName"
  outputFalsePath="$outputFolder/$apiOutputFolder"

  rm -rf "../${outputFolder:?}"

  java -jar "$apiGeneratorsFolder/openapi-generator-cli.jar" generate \
    -i "$apiDefinitionsFile" \
    -g "$apiLanguage" \
    -o "$rootDir/$outputFolder" \
    --package-name "$outputPackageName"

  mv "$rootDir/$outputFolder/$outputFolder/$outputName" "$rootDir/$outputFolder/$outputName"
  rm -rf "${rootDir:?}/${outputFalsePath:?}"

  pip3 install "$rootDir/$apiOutputFolder/$package"
done

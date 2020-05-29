#!/bin/bash
id=$(docker create agpypeline/agpyp:0.9.1) && docker cp $id:/code/ ./ && docker rm $id
mv ./code/SuperBuild/ ./
mv ./code/docker/ ./
mv ./code/modules/ ./
mv ./code/opendm/ ./
mv ./code/stages/ ./
cp ./actions_github/* ./
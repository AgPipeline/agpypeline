#!/bin/bash
id=$(docker create agpypeline/agpyp:0.9.1) && docker cp $id:/code/ ./ && docker rm $id
cp ./actions_github/* ./
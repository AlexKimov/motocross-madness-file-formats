#!/bin/bash
for f in ./*.tga; do echo -n "$f "; ./mcm2tool.out c "$f" ./ ; done 

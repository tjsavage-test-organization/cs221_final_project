#!/bin/bash
for num in {1..20}
do
	python capture.py -r qlearningAgent -Q
	cp FeatureWeights.py weights/$num
done	

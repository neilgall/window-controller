FUNCTION_ARN := arn:aws:lambda:eu-west-1:188024963716:function:fresh-air-handler
ZIP := build/lambda_function.zip

.PHONY: all
all: $(ZIP) upload

.PHONY: clean
clean:
	rm -rf build

$(ZIP): lambda_function.py
	mkdir -p build
	zip -r $@ alexa $<

upload: $(ZIP)
	aws lambda update-function-code \
		--function-name $(FUNCTION_ARN) \
		--zip-file fileb://$^ \

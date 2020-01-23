# GreenerPython
GreenerPython is an experiment in speeding up the TDD cycle, the red->green part of the cycle to be precise.
It does this by generating stubs based on unit tests.

Why TDD and why the red->green part of the cycle in particular?  
And how can we speed up this step?  
Don't IDEs already do this?

To anwer these questions, let's briefly discuss the following points:
* TDD and why it is interesting
* Existing tool support
* Going from red to green faster
* Don't IDEs already do this?

## TDD and why it is interesting
TDD consists of
* writing a failing test (because the function is not yet implemented)
* writing the code to make the test pass
* cleaning up the code

This is often summarized as red, green, refactor.
From a tool builder's perspective, this is interesting because it gives us a precise, executable specification.
It also gives us a well defined workflow that we can support.

## Existing tool support
Refactoring has pretty good IDE support.
Unit test frameworks support writing tests with a minimum of fuss.
This means we have two of the three TDD steps covered:
* red: unit test frameworks like JUnit and its ports
* green: ???
* refactor: IDE

Going from red to green requires actually writing code and that takes a lot of time.
Last time I checked, tool support for this step was not as good as it should be.

## Going from red to green faster
Every programmer wants to go from red to green as fast as possible.
So isn't this just wishful thinking about computers reading our minds and automagically generating code?

There is no such thing as a free lunch, so we must give up something to go faster.
What we give up is generality and we give it up in two ways:
* restrict ourselves to a TDD workflow
* restrict the kinds of stubs we generate

Restricting ourselves to a TDD workflow means that GreenerPython may do the wrong thing when used in a different workflow.
Restricting the kinds of stubs we generate means not trying to guess that the code should compute square roots, for example.

Having talked a lot about failure cases and limitations, what are the actual use cases that GreenerPython supports?
Within the system under test, it creates stubs for
* functions
* classes

Within those classes, it adds
* fields
* methods

## Don't IDEs already do this?
IDEs can already generate stubs, so what's the point?

The point is to generate stubs *without any typing or clicking*.
This might seem like a small improvement but it makes a big difference in practice.

The more general goal is to explore how fluid we can make the TDD cycle if we take it for granted.



#coding=utf8

# Copyright © 2012 Tim Radvan
# 
# This file is part of Kurt.
# 
# Kurt is free software: you can redistribute it and/or modify it under the 
# terms of the GNU Lesser General Public License as published by the Free 
# Software Foundation, either version 3 of the License, or (at your option) any 
# later version.
# 
# Kurt is distributed in the hope that it will be useful, but WITHOUT ANY 
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more 
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along 
# with Kurt. If not, see <http://www.gnu.org/licenses/>.

tests_run = 0
tests_failed = 0
test_results = {}


print 'Testing!'


def test_cons(cons, encoded, value):
    global tests_run, tests_failed
    failed = False
    
    def fail(failed=failed):
        if not failed:
            print 'Test #%i, %s:' % (tests_run, value)
        failed = True
    
    parsed = None
    try:
        parsed = cons.parse(encoded)
    except Exception, e:
        if not failed: fail()
        failed = True
        print '  Parse Error: %s' % e
    else:
        if not parsed == value or parsed != value: # Stupid but might forget to do __ne__ as well as __eq__...
            if not failed: fail()
            failed = True
            print '  %s.parse(%s) gave <%s> not <%s>' % (cons, repr(encoded), repr(parsed), repr(value))
    
    built = None
    try:
        built = cons.build(value)
    except Exception, e:
        if not failed: fail()
        failed = True
        print '  Build Error: %s' % e
    else:
        if not built == encoded or built != encoded:
            if not failed: fail()
            failed = True
            print '  %s.build(%s) gave <%s> not <%s>' % (cons, repr(value), repr(built), repr(encoded))
    
    if failed:
        tests_failed += 1
        test_results[tests_run] = (cons, encoded, value, parsed, built)
    tests_run += 1


def tests_finish():
    if tests_run:
        if tests_failed:
            print 'Failed %i of %i tests.' % (tests_failed, tests_run)
            print '(See results in test_results.)'
        else:
            print 'Ran all %i tests successfully!' % tests_run
    else:
        print 'No tests run!'
    print '###'
    print


def retry_test(index):
    test_cons(*test_results[index][:3])
    (cons, encoded, value) = test_results[index][:3]



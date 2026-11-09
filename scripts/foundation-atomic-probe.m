#import <Foundation/Foundation.h>

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc != 2) {
            fprintf(stderr, "usage: foundation-atomic-probe OUTPUT_DIR\n");
            return 64;
        }
        NSString *root = [NSString stringWithUTF8String:argv[1]];
        NSDictionary *record = @{ @"probe": @"synthetic", @"version": @1 };
        NSString *plain = [root stringByAppendingPathComponent:@"plain.plist"];
        NSString *atomic = [root stringByAppendingPathComponent:@"atomic.plist"];
        BOOL plainOK = [record writeToFile:plain atomically:NO];
        BOOL atomicOK = [record writeToFile:atomic atomically:YES];
        printf("{\"non_atomic\":%s,\"atomic\":%s}\n",
               plainOK ? "true" : "false", atomicOK ? "true" : "false");
        return plainOK && atomicOK ? 0 : 2;
    }
}

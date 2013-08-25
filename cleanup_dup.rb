#! /usr/bin/env ruby

# File: cleanup_dup.rb

# Clean up duplicate files in a specify directory.

require 'md5'
require 'fileutils'

DUP_DIR="./duplicates/"
LOG_FILE=DUP_DIR + "duplicates.log"

def main(directory)

  hash_table = Hash.new([])

  FileUtils.mkdir_p(DUP_DIR)
  log_file = open(LOG_FILE, "w+")
  
  Dir[directory.to_s + "**/**"].each do |f|
    if File.ftype(f) == "file"

      fo = File.open(f)
      check_sum = MD5.hexdigest(fo.read)
      fo.close

      if hash_table.has_key?(check_sum)
        puts "#{f} Duplicated to #{hash_table[check_sum]}"
        log_file.write("#{f} Duplicated to #{hash_table[check_sum]}\n")

        dirname = File.dirname(f)
        basename = File.basename(f)
        
        # Create a new dir in #{DUP_DIR}
        new_dir = DUP_DIR + dirname
        FileUtils.mkdir_p(new_dir)

        # Move the duplicated file to new dir
        FileUtils.mv(f, new_dir)

      else
        hash_table[check_sum] = f
      end
      #print "#{check_sum}:#{f}"
    end
  end

  log_file.close

end

if __FILE__ == $0
  main(ARGV[0])
end
